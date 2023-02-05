from sqlalchemy.ext.asyncio import AsyncSession

from database.base_unit_of_work import BaseUnitOfWork
from .repository.media_repository import MediaRepository
from .repository.queued_tweet_repository import QueuedTweetRepository
from .repository.saved_tweet_repository import SavedTweetRepository
from .repository.tweet_repository import TweetRepository
from .repository.user_repository import UserRepository
from .repository.video_version_repository import VideoVersionRepository


class UnitOfWork(BaseUnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

        self.tweets = TweetRepository(self._session)
        self.users = UserRepository(self._session)
        self.video_versions = VideoVersionRepository(self._session)
        self.media_files = MediaRepository(self._session)
        self.queued_tweets = QueuedTweetRepository(self._session)
        self.saved_tweets = SavedTweetRepository(self._session)
