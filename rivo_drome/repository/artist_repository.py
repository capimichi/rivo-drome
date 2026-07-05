from typing import Optional, List

from injector import inject

from rivo_drome.entity.artist import Artist
from rivo_drome.manager.db_manager import DbManager
from rivo_drome.repository.base_repository import BaseRepository


class ArtistRepository(BaseRepository):
    @inject
    def __init__(self, db_manager: DbManager):
        super().__init__(db_manager)

    @property
    def _entity_class(self):
        return Artist

    async def find_by_deezer_id(self, deezer_id: int) -> Optional[Artist]:
        return await self._run_sync(lambda: self._find_by_deezer_id_sync(deezer_id))

    def _find_by_deezer_id_sync(self, deezer_id: int) -> Optional[Artist]:
        with self._db_manager.create_session() as session:
            return session.query(Artist).filter(Artist.deezer_id == deezer_id).first()

    async def search_by_name(self, query: str, limit: int = 20) -> List[Artist]:
        return await self._run_sync(lambda: self._search_by_name_sync(query, limit))

    def _search_by_name_sync(self, query: str, limit: int = 20) -> List[Artist]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Artist)
                .filter(Artist.name.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )
