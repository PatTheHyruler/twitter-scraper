import mimetypes
import random
import re
import string
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
import tweepy
from bs4 import BeautifulSoup

from config import Config
from database.db import Database
from exceptions import TweetFetchFailedException
from model import UnitOfWork
from model.entity.media import EMediaType, Media
from model.entity.queued_tweet import QueuedTweet
from model.entity.saved_tweet import ESavedTweetType
from model.entity.tweet import Tweet
from model.entity.user import User
from model.entity.video_version import VideoVersion


class BirdArchiver:
    def __init__(self, db: Database, client: tweepy.Client = None, show_more_limit: int = 64):
        self._client = client
        # self.client = client if client is not None else tweepy.Client(Config.get().Twitter.BearerToken)
        self.database = db
        self.show_more_limit = show_more_limit
        self.uow = UnitOfWork(self.database.session)
        self._processing_tweets_ids: List[int] = []
        self._processed_tweets_ids: List[int] = []

    @property
    def client(self):
        if self._client is None:
            self._client = tweepy.Client(Config.get().Twitter.UserAccessToken, wait_on_rate_limit=True)
        return self._client

    @staticmethod
    def ask_user_for_new_user_access_token() -> str:
        oauth_2_user_handler = tweepy.OAuth2UserHandler(
            client_id=Config.get().Twitter.ClientId,
            client_secret=Config.get().Twitter.ClientSecret,
            redirect_uri=Config.get().Twitter.RedirectURI,
            scope=['tweet.read', 'users.read', 'follows.read', 'offline.access', 'like.read', 'bookmark.read']
        )
        authorization_response_url = input(
            f"Click on this link and then click Authorize app:\n{oauth_2_user_handler.get_authorization_url()}\n"
            f"Now paste the contents of your browser's URL bar here:\n")
        access_token = oauth_2_user_handler.fetch_token(authorization_response_url)["access_token"]
        return access_token

    @classmethod
    def refresh_and_save_bot_user_access_token(cls):
        access_token = cls.ask_user_for_new_user_access_token()
        Config.get().Twitter.UserAccessToken = access_token
        Config.save()

    def __fetch_user(self, user_id: int) -> tweepy.User:
        return self.client.get_user(id=user_id,
                                              user_fields=['created_at', 'description', 'entities', 'location',
                                                           'profile_image_url', 'public_metrics', 'url',
                                                           'verified', 'pinned_tweet_id']).data

    async def archive_user(self, uow: UnitOfWork, user_id: int) -> User:
        existing_user = await uow.users.get_by_user_id(user_id)
        if existing_user is None:
            user = self.__fetch_user(user_id)
            return await uow.users.add(User(user))
        else:
            return existing_user

    def __fetch_tweet(self, tweet_id: int) -> tweepy.Response:
        return self.client.get_tweet(id=tweet_id, expansions=['attachments.media_keys'],
                                               tweet_fields=['public_metrics', 'referenced_tweets', 'entities',
                                                             'conversation_id', 'in_reply_to_user_id', 'author_id',
                                                             'created_at'],
                                               media_fields=['type', 'url', 'public_metrics', 'alt_text', 'variants'])

    def __get_simple_user(self, username: str) -> tweepy.user.User:
        return self.client.get_user(username=username).data

    def __get_users_tweets(self, user_id: int, pagination_token: str = None) -> tweepy.Response:
        return self.client.get_users_tweets(id=user_id, pagination_token=pagination_token)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.database.session.close()
        if self._client:
            self._client.session.close()

    @staticmethod
    async def get_tweet_nitter_links(tweet: Tweet, author_username: str) -> List[str]:
        return [f"https://{instance_url}/{author_username}/status/{tweet.id}" for instance_url in Config.get().Nitter.InstanceURLs]

    async def add_tweet_replies_to_queue(self, uow: UnitOfWork, tweet: Tweet, author_username: str, priority: int) -> bool:
        urls = await self.get_tweet_nitter_links(tweet, author_username)

        pattern = r"\/.+\/status\/(\d+)"

        sufficient_replies_added = lambda replies: len(replies) >= 0.6 * tweet.reply_count

        added_replies = set()
        print(f"Finding replies for {tweet}")
        for url in urls:
            print(f"{url=}")
            base_url = url
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
                            await self._add_tweet_to_queue(uow, reply_id, priority)
                            added_replies.add(reply_id)
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
            if sufficient_replies_added(added_replies):
                break
        print(f"{len(added_replies)} of {tweet.reply_count} replies for tweet id {tweet.id} added to queue")
        return sufficient_replies_added(added_replies)

    @staticmethod
    def download_media(url: str) -> Path:
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

    async def add_referenced_tweets_to_queue(self, uow: UnitOfWork, tweet: tweepy.Tweet, priority):
        if tweet.referenced_tweets is not None:
            for referenced_tweet in tweet.referenced_tweets:
                await self._add_tweet_to_queue(uow, referenced_tweet.id, priority)

    async def archive_queued_tweet(self, uow: UnitOfWork, queued_tweet: QueuedTweet):
        tweet: tweepy.Tweet
        response = self.__fetch_tweet(queued_tweet.tweet_id)
        tweet = response.data
        if tweet is None:
            raise TweetFetchFailedException(queued_tweet.tweet_id)

        db_tweet = Tweet(tweet)
        if queued_tweet.priority > 0:
            db_tweet.added_directly = True
        db_tweet.last_fetched = datetime.utcnow()

        user = await self.archive_user(uow, tweet.author_id)

        existing_archived_tweet = await uow.tweets.get_by_tweet_id(queued_tweet.tweet_id)
        if existing_archived_tweet is not None:
            db_tweet.db_id = existing_archived_tweet.db_id
            if existing_archived_tweet.added_directly is True:
                db_tweet.added_directly = True
            await uow.tweets.update_entity(db_tweet)
        else:
            await uow.tweets.add(db_tweet)

        replies_success = await self.add_tweet_replies_to_queue(uow, db_tweet, user.username, queued_tweet.priority - 1)
        await self.add_referenced_tweets_to_queue(uow, tweet, queued_tweet.priority - 1)

        if 'media' in response.includes:
            for media in response.includes['media']:
                media: tweepy.Media
                await self.uow.media_files.add(Media(media, tweet_id=queued_tweet.tweet_id))
                if (media.type == str(EMediaType.VIDEO.name).lower() or media.type == str(
                        EMediaType.ANIMATED_GIF.name).lower()) and media.variants is not None:
                    for variant_data in media.variants:
                        await self.uow.video_versions.add(VideoVersion(variant_data, media.media_key))

        if replies_success:
            await uow.queued_tweets.remove(queued_tweet)
        else:
            queued_tweet.replies_failed = True
            await uow.queued_tweets.update_entity(queued_tweet)
        await uow.save_changes()

    @staticmethod
    async def _add_tweet_to_queue(uow: UnitOfWork, tweet_id: int, priority: int = 0):
        await uow.queued_tweets.add_to_queue(tweet_id, priority)

    async def add_tweets_to_queue(self, tweet_ids: List):
        uow = UnitOfWork(self.database.session)
        for arg in tweet_ids:
            try:
                tweet_id = int(arg)
                await self._add_tweet_to_queue(uow, tweet_id, 1)
            except Exception as e:
                print(e)
        await uow.save_changes()

    async def add_user_tweets_to_queue(self, username: str):
        user = self.__get_simple_user(username)
        uow = UnitOfWork(self.database.session)

        await self.archive_user(uow, user.id)

        next_token = None
        while True:
            response = self.__get_users_tweets(user.id, next_token)
            if not response.data:
                break
            for tweet in response.data:
                tweet: tweepy.Tweet
                await self._add_tweet_to_queue(uow, tweet.id)
            if 'next_token' in response.meta:
                next_token = response.meta['next_token']
            else:
                break
        await uow.save_changes()

    async def add_bookmarks_to_queue(self, requeue_old: bool = False):
        print("adding bookmarks to queue")
        uow = UnitOfWork(self.database.session)
        next_token = None
        user = self.client.get_me(user_auth=False)
        user_id = user.data["id"]
        while True:
            response = self.client.get_bookmarks(pagination_token=next_token)
            for tweet in response.data:
                changes_made = await uow.saved_tweets.mark_tweet_saved(tweet.id, user_id, ESavedTweetType.BOOKMARK)
                if requeue_old or not (await uow.tweets.exists_by_tweet_id(tweet.id) or await uow.queued_tweets.exists_by_tweet_id(tweet.id)):
                    changes_made = True
                    await self._add_tweet_to_queue(uow, tweet.id)
                if changes_made:
                    await uow.save_changes()
            if 'next_token' in response.meta:
                next_token = response.meta['next_token']
            else:
                break
        print("finished adding bookmarks to queue")

    async def archive_tweets_from_queue(self, total: Optional[int] = None, min_priority: int = -6, batch_size: int = 10, retry_failed: bool = False):
        archived = 0
        started = datetime.utcnow()
        while total is None or archived < total:
            uow = UnitOfWork(self.database.session)
            queued_tweets = await uow.queued_tweets.get_next(batch_size, min_priority, retry_failed, started)
            for queued_tweet in queued_tweets:
                try:
                    await self.archive_queued_tweet(uow, queued_tweet)
                except TweetFetchFailedException as e:
                    queued_tweet.tweet_failed = True
                    print(f"Failed to fetch {queued_tweet}!")
                    await uow.queued_tweets.update_entity(queued_tweet)
                    await uow.save_changes()
                archived += 1
            if len(queued_tweets) == 0:
                return

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
