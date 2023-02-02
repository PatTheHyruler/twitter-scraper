from typing import Type, List

from sqlalchemy import select

from database.base_repository import BaseRepository, TEntity
from ..entity.user import User


class UserRepository(BaseRepository[User]):
    @property
    def _table(self) -> Type[TEntity]:
        return User

    async def get_all_without_media(self) -> List[User]:
        stmt = select(self._table).where(self._table.profile_image_downloaded == 0)
        result = await self._execute_scalars(stmt)
        return result.all()
