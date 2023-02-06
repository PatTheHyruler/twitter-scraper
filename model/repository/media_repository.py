from typing import Type, List

from sqlalchemy import select

from database.base_repository import BaseRepository, TEntity
from utils import get_class_fields
from ..entity.media import Media


class MediaRepository(BaseRepository[Media]):
    @property
    def _table(self) -> Type[TEntity]:
        return Media

    async def get_all_not_downloaded(self) -> List[Media]:
        stmt = select(self._table).where(self._table.downloaded == 0).where(self._table.url.is_not(None))
        result = await self._execute_scalars(stmt)
        return result.unique().all()

    async def update_entity(self, entity: TEntity) -> TEntity:
        class_fields = get_class_fields(entity)
        if 'variants' in class_fields:
            class_fields.pop('variants')
        return await self.update(entity.db_id, class_fields)
