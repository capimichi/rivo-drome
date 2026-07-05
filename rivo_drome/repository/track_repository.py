from typing import Optional, List

from injector import inject

from rivo_drome.entity.track import Track
from rivo_drome.manager.db_manager import DbManager
from rivo_drome.repository.base_repository import BaseRepository


class TrackRepository(BaseRepository):
    @inject
    def __init__(self, db_manager: DbManager):
        super().__init__(db_manager)

    @property
    def _entity_class(self):
        return Track

    async def find_by_deezer_id(self, deezer_id: int) -> Optional[Track]:
        return await self._run_sync(lambda: self._find_by_deezer_id_sync(deezer_id))

    def _find_by_deezer_id_sync(self, deezer_id: int) -> Optional[Track]:
        with self._db_manager.create_session() as session:
            return session.query(Track).filter(Track.deezer_id == deezer_id).first()

    async def search_by_title(self, query: str, limit: int = 20) -> List[Track]:
        return await self._run_sync(lambda: self._search_by_title_sync(query, limit))

    def _search_by_title_sync(self, query: str, limit: int = 20) -> List[Track]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Track)
                .filter(Track.title.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )

    async def find_by_album(self, album_id: int) -> List[Track]:
        return await self._run_sync(lambda: self._find_by_album_sync(album_id))

    def _find_by_album_sync(self, album_id: int) -> List[Track]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Track)
                .filter(Track.album_id == album_id)
                .order_by(Track.track_number)
                .all()
            )

    async def find_by_artist(self, artist_id: int) -> List[Track]:
        return await self._run_sync(lambda: self._find_by_artist_sync(artist_id))

    def _find_by_artist_sync(self, artist_id: int) -> List[Track]:
        with self._db_manager.create_session() as session:
            return (
                session.query(Track)
                .filter(Track.artist_id == artist_id)
                .all()
            )
