from typing import Type, Optional

from sqlalchemy import select

from database.base_repository import BaseRepository, TEntity
from ..entity.saved_tweet import SavedTweet, ESavedTweetType


class SavedTweetRepository(BaseRepository[SavedTweet]):
    @property
    def _table(self) -> Type[TEntity]:
        return SavedTweet

    async def get_by_tweet_id_and_user_id(self, tweet_id: int, user_id: int) -> Optional[SavedTweet]:
        stmt = select(self._table).where(self._table.tweet_id == tweet_id and self._table.user_id == user_id)
        return await self._first(stmt)

    async def mark_tweet_saved(self, tweet_id: int, user_id: int, saved_type: ESavedTweetType) -> bool:
        saved_tweet = await self.get_by_tweet_id_and_user_id(tweet_id, user_id)
        if saved_tweet is None:
            await self.add(SavedTweet(tweet_id, user_id, saved_type))
            return True
        return False
