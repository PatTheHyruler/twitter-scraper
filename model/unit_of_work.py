from sqlalchemy.ext.asyncio import AsyncSession

from database.base_unit_of_work import BaseUnitOfWork
from .repository.media_repository import MediaRepository
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
