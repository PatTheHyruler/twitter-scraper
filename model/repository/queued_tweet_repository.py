from typing import Type, List, Optional

from sqlalchemy import select, exists

from database.base_repository import BaseRepository, TEntity
from ..entity.queued_tweet import QueuedTweet


class QueuedTweetRepository(BaseRepository[QueuedTweet]):
    @property
    def _table(self) -> Type[TEntity]:
        return QueuedTweet

    async def get_by_tweet_id(self, tweet_id: int) -> Optional[QueuedTweet]:
        stmt = select(self._table).where(self._table.tweet_id == tweet_id)
        return await self._first(stmt)

    async def get_next(self, amount: int, min_priority: int, retry_failed: bool) -> List[QueuedTweet]:
        stmt = select(self._table)
        stmt = stmt.where(self._table.priority >= min_priority)
        if not retry_failed:
            stmt = stmt.where(self._table.tweet_failed.is_(False) & self._table.replies_failed.is_(False))
        stmt = stmt.order_by(self._table.priority.desc()).limit(amount)
        return await self._all(stmt)

    async def add_to_queue(self, tweet_id: int, priority: int = 0):
        queued_tweet = await self.get_by_tweet_id(tweet_id)
        if queued_tweet is None:
            queued_tweet = QueuedTweet(tweet_id, priority)
        else:
            queued_tweet.priority = priority

        await self.upsert(queued_tweet)

    async def exists_by_tweet_id(self, tweet_id: int) -> bool:
        stmt = select(self._table).where(self._table.tweet_id == tweet_id)
        stmt = exists(stmt).select()
        result = await self._execute_scalars(stmt)
        return result.one()
