import argparse
import asyncio
import platform
from asyncio import AbstractEventLoop

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

    async with BirdArchiver(database) as ba:
        if args.tweet:
            for tweet_id in args.tweet:
                await ba.archive_tweet(int(tweet_id))

        if args.user:
            for user_handle in args.user:
                await ba.archive_user_tweets(user_handle)

        if args.bookmarks:
            await ba.archive_bookmarks()

        if args.media:
            await ba.download_all_media()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--bookmarks", help="Archive authenticated user's bookmarks.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--media", help="Download any non-downloaded media for all archived tweets and users.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--tweet", help="Archive specified tweet ID", action='append', type=int)
    parser.add_argument("--user", help="Archive specified twitter user handle", action='append', type=str)

    try:
        asyncio.run(startup(parser.parse_args()))
    except KeyboardInterrupt:
        pass
