from typing import Type, List

from sqlalchemy import select

from database.base_repository import BaseRepository, TEntity
from ..entity.video_version import VideoVersion


class VideoVersionRepository(BaseRepository[VideoVersion]):
    @property
    def _table(self) -> Type[TEntity]:
        return VideoVersion

    async def get_all_not_downloaded(self) -> List[VideoVersion]:
        stmt = select(self._table).where(self._table.downloaded == 0)
        result = await self._execute_scalars(stmt)
        return result.all()
