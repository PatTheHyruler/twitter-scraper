import mimetypes
import os
import random
import re
import string
from pathlib import Path
from typing import List, Optional

import requests
import tweepy
from bs4 import BeautifulSoup

from config import Config
from database.db import Database
from model import UnitOfWork
from model.entity.media import EMediaType, Media
from model.entity.tweet import Tweet
from model.entity.user import User
from model.entity.video_version import VideoVersion


class BirdArchiver:
    def __init__(self, db: Database, client: tweepy.Client = None, show_more_limit: int = 12):
        self._client = client
        self.database = db
        self.show_more_limit = show_more_limit
        self.uow = UnitOfWork(self.database.session)
        self._processing_tweets_ids: List[int] = []
        self._processed_tweets_ids: List[int] = []

    @property
    def client(self) -> tweepy.Client:
        if self._client is None:
            self._client = tweepy.Client(Config.get().Twitter.UserAccessToken)

        return self._client

    @staticmethod
    def ask_user_for_new_user_access_token() -> tweepy.Client:
        oauth_2_user_handler = tweepy.OAuth2UserHandler(
            client_id=Config.get().Twitter.ClientId,
            client_secret=Config.get().Twitter.ClientSecret,
            redirect_uri=Config.get().Twitter.RedirectURI,
            scope=['tweet.read', 'users.read', 'follows.read', 'offline.access', 'like.read', 'bookmark.read']
        )
        authorization_response_url = input(
            f"Click on this link and then click Authorize app:\n{oauth_2_user_handler.get_authorization_url()}\n"
            f"Now paste the contents of your browser's URL bar here:\n")
        access_token = oauth_2_user_handler.fetch_token(authorization_response_url)
        try:
            Config.get().Twitter.UserAccessToken = access_token['access_token']
            Config.save()
        except Exception as e:
            print(f"Failed to save access token to config:\n{e}")
        return tweepy.Client(access_token['access_token'])

    async def is_archived(self, tweet_id: int) -> bool:
        return tweet_id in self._processing_tweets_ids \
               or tweet_id in self._processed_tweets_ids \
               or await self.uow.tweets.exists(tweet_id)

    def __get_user(self, user_id: int) -> tweepy.User:
        l = lambda u_id: self.client.get_user(id=user_id,
                                              user_fields=['created_at', 'description', 'entities', 'location',
                                                           'profile_image_url', 'public_metrics', 'url',
                                                           'verified', 'pinned_tweet_id']).data
        try:
            return l(user_id)
        except tweepy.errors.Unauthorized:
            self.ask_user_for_new_user_access_token()
            return l(user_id)

    async def archive_user(self, user_id: int):
        if not await self.uow.users.exists(user_id):
            user = self.__get_user(user_id)
            await self.uow.users.add(User(user))
            await self.uow.save_changes()

    def __get_tweet(self, tweet_id: int) -> tweepy.Response:
        l = lambda t_id: self.client.get_tweet(id=tweet_id, expansions=['attachments.media_keys'],
                                               tweet_fields=['public_metrics', 'referenced_tweets', 'entities',
                                                             'conversation_id', 'in_reply_to_user_id', 'author_id',
                                                             'created_at'],
                                               media_fields=['type', 'url', 'public_metrics', 'alt_text', 'variants'])
        try:
            return l(tweet_id)
        except tweepy.errors.Unauthorized:
            self.ask_user_for_new_user_access_token()
            return l(tweet_id)

    async def archive_tweet(self, tweet_id: int, depth_left: int = 15) -> bool:
        if await self.is_archived(tweet_id):
            return True
        if depth_left <= 0:
            return False

        tweet: Optional[tweepy.Tweet] = None
        response = None
        for i in range(2):
            response = self.__get_tweet(tweet_id)
            tweet = response.data
            if tweet is not None:
                break
        if tweet is None:
            print(f"Tweet ID {tweet_id} returned None from Twitter")
            return False

        self._processing_tweets_ids.append(tweet_id)

        await self.archive_user(tweet.author_id)

        if tweet.referenced_tweets is not None:
            successfully_archived_referenced_tweets = True
            try:
                for ref_tweet in tweet.referenced_tweets:
                    success = await self.archive_tweet(int(ref_tweet['id']), depth_left - 1)
                    successfully_archived_referenced_tweets = successfully_archived_referenced_tweets and success
            except Exception as e:
                print(f"Failed to archive referenced tweets for {tweet}\n{e}")
                tweet.referenced_tweets = []
            if not successfully_archived_referenced_tweets:
                tweet.referenced_tweets = []

        if tweet.conversation_id:
            if not await self.is_archived(tweet.conversation_id):
                tweet.conversation_id = None

        if 'media' in response.includes:
            for media in response.includes['media']:
                media: tweepy.Media
                await self.uow.media_files.add(Media(media, tweet_id=tweet_id))
                if (media.type == str(EMediaType.VIDEO.name).lower() or media.type == str(
                        EMediaType.ANIMATED_GIF.name).lower()) and media.variants is not None:
                    for variant_data in media.variants:
                        await self.uow.video_versions.add(VideoVersion(variant_data, media.media_key))

        await self.uow.tweets.add(Tweet(tweet))
        self._processing_tweets_ids.remove(tweet_id)

        if await self.uow.save_changes():
            self._processed_tweets_ids.append(tweet_id)

            await self._archive_tweet_replies(tweet_id)

            return True

        return False

    def __get_bookmarks(self, pagination_token: str) -> tweepy.Response:
        try:
            return self.client.get_bookmarks(pagination_token=pagination_token)
        except tweepy.errors.Unauthorized:
            self._client = self.ask_user_for_new_user_access_token()
            return self.client.get_bookmarks(pagination_token=pagination_token)

    async def archive_bookmarks(self):
        print("archiving bookmarks")
        next_token = None
        while True:
            response = self.__get_bookmarks(next_token)
            for tweet in response.data:
                await self.archive_tweet(tweet.id)
            if 'next_token' in response.meta:
                next_token = response.meta['next_token']
            else:
                break
        print("done")

    def __get_simple_user(self, username: str) -> tweepy.user.User:
        try:
            return self.client.get_user(username=username).data
        except tweepy.errors.Unauthorized:
            self.ask_user_for_new_user_access_token()
            return self.client.get_user(username=username).data

    def __get_users_tweets(self, user_id: int, pagination_token: str = None) -> tweepy.Response:
        try:
            return self.client.get_users_tweets(id=user_id, pagination_token=pagination_token)
        except tweepy.errors.Unauthorized:
            self.ask_user_for_new_user_access_token()
            return self.client.get_users_tweets(id=user_id, pagination_token=pagination_token)

    async def archive_user_tweets(self, username: str):
        user = self.__get_simple_user(username)

        await self.archive_user(user.id)

        next_token = None
        while True:
            response = self.__get_users_tweets(user.id, next_token)
            for tweet in response.data:
                tweet: tweepy.Tweet
                await self.archive_tweet(tweet.id)
            if 'next_token' in response.meta:
                next_token = response.meta['next_token']
            else:
                break

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.database.session.close()

    @staticmethod
    async def get_tweet_nitter_link(tweet: Tweet) -> str:
        return f"https://nitter.net/{tweet.author.username}/status/{tweet.id}"

    async def _archive_tweet_replies(self, tweet_id: int):
        try:
            tweet = await self.uow.tweets.get_by_id(tweet_id)
            url = await self.get_tweet_nitter_link(tweet)
        except Exception as e:
            print(f"Failed to get replies for tweet {tweet_id}!\n{e}")
            return

        pattern = r"\/.+\/status\/(\d+)"
        base_url = url
        added_replies = 0
        while url is not None:
            try:
                r = requests.get(url)
            except Exception:
                break
            url = None
            try:
                soup = BeautifulSoup(r.content)
                link_elements = soup.find_all('a', class_='tweet-link')
            except Exception:
                break
            for link_element in link_elements:
                try:
                    reply_url = link_element['href']
                    m = re.match(pattern, reply_url)
                    if m:
                        reply_id = int(m.group(1))
                        if await self.archive_tweet(reply_id):
                            added_replies += 1
                except Exception as e:
                    print(f"Failed to archive reply from '{link_element}'\n{e}")
                    continue
            show_more = 0
            for div in soup.find_all('div', class_='show-more'):
                show_more += 1
                if show_more > self.show_more_limit:
                    break
                for link_element in div.find_all('a'):
                    try:
                        additional_url = link_element['href']
                        if len(additional_url) > 0:
                            url = base_url + additional_url
                        break
                    except Exception:
                        continue
                if url is not None:
                    break
        print(f"{added_replies} replies for tweet id {tweet_id} are archived")

    async def download_all_media(self):
        print("downloading media")
        for user in await self.uow.users.get_all_without_media():
            try:
                file_path = self.download_media(user.profile_image_url)
                user.profile_image_downloaded = True
                user.profile_image_file_path = file_path
                await self.uow.users.update_entity(user)
                await self.uow.save_changes()
            except Exception as e:
                print(f"Failed to download PFP for {user}\n{e}")

        for media in await self.uow.media_files.get_all_not_downloaded():
            try:
                file_path = self.download_media(media.url)
                media.downloaded = True
                media.file_path = file_path
                await self.uow.media_files.update_entity(media)
                await self.uow.save_changes()
            except Exception as e:
                print(f"Failed to download media file for {media}\n{e}")

        for video_version in await self.uow.video_versions.get_all_not_downloaded():
            try:
                file_path = self.download_media(video_version.url)
                video_version.downloaded = True
                video_version.file_path = file_path
                await self.uow.video_versions.update_entity(video_version)
                await self.uow.save_changes()
            except Exception as e:
                print(f"Failed to download media file for {video_version}\n{e}")
        print("media downloaded")

    @staticmethod
    def download_media(url: str) -> Path:
        """Go through archived tweets and users in database and download their included media"""

        media_path = Path(Config.get().Media.Path)

        response_gotten = False
        response: requests.Response
        if "profile_images" in url:
            replaced_url = url.replace("_normal", "_400x400")
            response = requests.get(replaced_url)
            if response.status_code == 200:
                response_gotten = True
                url = replaced_url
        if not response_gotten:
            response = requests.get(url)

        content_type = response.headers.get('content-type')
        extension = ""
        guessed = False
        if content_type is not None:
            extension_guess = mimetypes.guess_extension(content_type)
            if extension_guess is not None:
                guessed = True
                extension += extension_guess
        if not guessed:
            if ".m3u8" in url:
                extension += ".m3u8"

        file_name = str(abs(url.__hash__())) + "_" + ''.join(
            random.choices(string.ascii_letters + string.digits, k=8)) + extension
        file_path = media_path / Path(file_name)
        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"Downloaded {url} to {file_path}")
        return file_path
