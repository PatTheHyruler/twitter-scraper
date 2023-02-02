from typing import Type

from database.base_repository import BaseRepository, TEntity
from ..entity.tweet import Tweet


class TweetRepository(BaseRepository[Tweet]):
    @property
    def _table(self) -> Type[TEntity]:
        return Tweet
