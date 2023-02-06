import argparse
import asyncio

import tweepy

from bird_archiver import BirdArchiver
from config import Config
from database.db import Database


def get_database() -> Database:
    """Configure and get database object.

    init() must be called on resulting database object.
    """
    database_host = Config.get().Database.Host
    database_user = Config.get().Database.User
    database_password = Config.get().Database.Password
    database_name = Config.get().Database.Name

    database = Database(
        f"mariadb+asyncmy://{database_user}:{database_password}@{database_host}/{database_name}?charset=utf8mb4")

    return database


async def startup(args: argparse.Namespace):
    database = get_database()

    await database.init()

    client = None
    if args.bookmarks:
        access_token = BirdArchiver.ask_user_for_new_user_access_token()
        client = tweepy.Client(access_token)

    async with BirdArchiver(database, client=client) as ba:
        if args.tweet:
            await ba.add_tweets_to_queue(args.tweet)
        elif args.user:
            for user_handle in args.user:
                await ba.add_user_tweets_to_queue(user_handle)
        elif args.bookmarks:
            await ba.add_bookmarks_to_queue(True if args.requeueold else False)
        elif args.media:
            await ba.download_all_media()
        elif args.reauth:
            ba.refresh_and_save_bot_user_access_token()
        else:
            archive_count = None
            if args.archivecount:
                archive_count = int(args.archivecount)
            min_priority = -6
            if args.minpriority:
                min_priority = int(args.minpriority)
            await ba.archive_tweets_from_queue(archive_count, min_priority)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-b", "--bookmarks", help="Queue bookmarks (prompts authorization).",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-r", "--requeueold", help="Requeue already archived bookmarks (use with --bookmarks)")
    parser.add_argument("--media", help="Download any non-downloaded media for all archived tweets and users.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-t", "--tweet", help="Queue specified tweet ID", action='append', type=int)
    parser.add_argument("--user", help="Queue specified twitter user handle", action='append', type=str)
    parser.add_argument("-ac", "--archivecount", help="Amount of tweets to archive from queue", type=int)
    parser.add_argument("-min", "--minpriority", help="Priority cutoff below which tweets shouldn't be archived", type=int)
    parser.add_argument("--reauth", help="Reauthenticate bot user", action=argparse.BooleanOptionalAction)


    try:
        asyncio.run(startup(parser.parse_args()))
    except KeyboardInterrupt:
        pass
