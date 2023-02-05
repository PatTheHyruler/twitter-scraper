from typing import Type, Optional

from sqlalchemy import select, exists

from database.base_repository import BaseRepository, TEntity
from ..entity.tweet import Tweet


class TweetRepository(BaseRepository[Tweet]):
    @property
    def _table(self) -> Type[TEntity]:
        return Tweet

    async def get_by_tweet_id(self, tweet_id: int) -> Optional[Tweet]:
        stmt = select(self._table).where(self._table.id == tweet_id)
        return await self._first(stmt)

    async def exists_by_tweet_id(self, tweet_id: int) -> bool:
        stmt = select(self._table).where(self._table.id == tweet_id)
        stmt = exists(stmt).select()
        result = await self._execute_scalars(stmt)
        return result.one()
