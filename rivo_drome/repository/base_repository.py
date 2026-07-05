import asyncio
from abc import ABC, abstractmethod
from typing import Type, Optional, List

from sqlalchemy.orm import Session

from rivo_drome.entity.base import BaseEntity
from rivo_drome.manager.db_manager import DbManager


class BaseRepository(ABC):
    def __init__(self, db_manager: DbManager):
        self._db_manager = db_manager

    async def _run_sync(self, fn):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, fn)

    @property
    @abstractmethod
    def _entity_class(self) -> Type[BaseEntity]:
        pass

    async def get_by_id(self, entity_id: int) -> Optional[BaseEntity]:
        return await self._run_sync(lambda: self._get_by_id_sync(entity_id))

    def _get_by_id_sync(self, entity_id: int) -> Optional[BaseEntity]:
        with self._db_manager.create_session() as session:
            return session.get(self._entity_class, entity_id)

    async def save(self, entity: BaseEntity) -> BaseEntity:
        return await self._run_sync(lambda: self._save_sync(entity))

    def _save_sync(self, entity: BaseEntity) -> BaseEntity:
        with self._db_manager.create_session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    async def delete(self, entity: BaseEntity) -> None:
        await self._run_sync(lambda: self._delete_sync(entity))

    def _delete_sync(self, entity: BaseEntity) -> None:
        with self._db_manager.create_session() as session:
            session.delete(entity)
            session.commit()

    async def list_all(self) -> List[BaseEntity]:
        return await self._run_sync(lambda: self._list_all_sync())

    def _list_all_sync(self) -> List[BaseEntity]:
        with self._db_manager.create_session() as session:
            return session.query(self._entity_class).all()
