from abc import ABCMeta
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

TEntity = TypeVar("TEntity")


class BaseUnitOfWork(metaclass=ABCMeta):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def refresh(self, entity: TEntity) -> TEntity:
        print(entity, "Refreshing entity")

        await self._session.refresh(entity)
        return entity

    async def commit(self):
        print("Committing changes")

        await self._session.commit()

    async def rollback(self):
        print("Rolling back changes")

        await self._session.rollback()

    async def close(self):
        print("Closing session")

        await self._session.close()

    async def save_changes(self) -> bool:
        try:
            await self.commit()
            return True
        except Exception as error:
            print(f"Transaction failed: {error}")
            await self.rollback()
            return False
