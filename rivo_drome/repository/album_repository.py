from typing import Optional, List

from injector import inject

from rivo_drome.entity.album import Album
from rivo_drome.manager.db_manager import DbManager
from rivo_drome.repository.base_repository import BaseRepository


class AlbumRepository(BaseRepository):
    @inject
    def __init__(self, db_manager: DbManager):
        super().__init__(db_manager)

    @property
    def _entity_class(self):
        return Album

    async def find_by_deezer_id(self, deezer_id: int) -> Optional[Album]:
        return await self._run_sync(lambda: self._find_by_deezer_id_sync(deezer_id))

    def _find_by_deezer_id_sync(self, deezer_id: int) -> Optional[Album]:
        with self._db_manager.create_session() as session:
            return session.query(Album).filter(Album.deezer_id == deezer_id).first()

    async def search_by_title(self, query: str, limit: int = 20) -> List[Album]:
        return await self._run_sync(lambda: self._search_by_title_sync(query, limit))

    def _search_by_title_sync(self, query: str, limit: int = 20) -> List[Album]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Album)
                .filter(Album.title.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )

    async def find_by_artist(self, artist_id: int) -> List[Album]:
        return await self._run_sync(lambda: self._find_by_artist_sync(artist_id))

    def _find_by_artist_sync(self, artist_id: int) -> List[Album]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Album)
                .filter(Album.artist_id == artist_id)
                .all()
            )
