from typing import List

from injector import inject
from rivo_drome.client.deezer_client import DeezerClient
from rivo_drome.entity.album import Album
from rivo_drome.entity.artist import Artist
from rivo_drome.entity.track import Track
from rivo_drome.model.subsonic_schema import (
    SearchResult3,
    SubsonicArtist,
    SubsonicAlbum,
    SubsonicChild,
)
from rivo_drome.repository.album_repository import AlbumRepository
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.track_repository import TrackRepository


class SearchService:
    @inject
    def __init__(
        self,
        deezer_client: DeezerClient,
        artist_repository: ArtistRepository,
        album_repository: AlbumRepository,
        track_repository: TrackRepository,
    ):
        self._deezer = deezer_client
        self._artist_repo = artist_repository
        self._album_repo = album_repository
        self._track_repo = track_repository

    async def search(self, query: str, artist_count: int = 20, album_count: int = 20, song_count: int = 20) -> SearchResult3:
        deezer_data = await self._deezer.search(query, limit=25)

        artists = []
        albums = []
        tracks = []

        for item in deezer_data.get("data", []):
            await self._process_deezer_item(item, artists, albums, tracks)

        return SearchResult3(
            artist=artists[:artist_count],
            album=albums[:album_count],
            song=tracks[:song_count],
        )

    async def _process_deezer_item(
        self,
        item: dict,
        artists: List[SubsonicArtist],
        albums: List[SubsonicAlbum],
        tracks: List[SubsonicChild],
    ):
        deezer_artist = item.get("artist", {})
        deezer_album = item.get("album", {})

        artist_id = None
        if deezer_artist.get("id"):
            artist = await self._get_or_create_artist(deezer_artist)
            artist_id = artist.id
            artists.append(self._artist_to_subsonic(artist))

        if deezer_album.get("id") and artist_id:
            album = await self._get_or_create_album(deezer_album, artist_id)
            albums.append(self._album_to_subsonic(album))

        if item.get("id") and artist_id:
            album_id = None
            if deezer_album.get("id"):
                album_entity = await self._get_or_create_album(deezer_album, artist_id)
                album_id = album_entity.id

            track = await self._get_or_create_track(item, artist_id, album_id)
            tracks.append(self._track_to_subsonic(track))

    async def _get_or_create_artist(self, deezer_artist: dict) -> Artist:
        deezer_id = deezer_artist["id"]
        existing = await self._artist_repo.find_by_deezer_id(deezer_id)
        if existing:
            return existing

        artist = Artist(
            name=deezer_artist.get("name", "Unknown"),
            picture_url=deezer_artist.get("picture_big") or deezer_artist.get("picture_medium"),
            deezer_id=deezer_id,
        )
        return await self._artist_repo.save(artist)

    async def _get_or_create_album(self, deezer_album: dict, artist_id: int) -> Album:
        deezer_id = deezer_album.get("id")
        if deezer_id:
            existing = await self._album_repo.find_by_deezer_id(deezer_id)
            if existing:
                return existing

        album = Album(
            title=deezer_album.get("title", "Unknown"),
            artist_id=artist_id,
            cover_url=deezer_album.get("cover_big") or deezer_album.get("cover_medium"),
            deezer_id=deezer_id,
        )
        return await self._album_repo.save(album)

    async def _get_or_create_track(self, item: dict, artist_id: int, album_id: int | None) -> Track:
        deezer_id = item.get("id")
        if deezer_id:
            existing = await self._track_repo.find_by_deezer_id(deezer_id)
            if existing:
                return existing

        track = Track(
            title=item.get("title", "Unknown"),
            artist_id=artist_id,
            album_id=album_id,
            duration=item.get("duration"),
            track_number=item.get("track_position"),
            deezer_id=deezer_id,
            status="pending",
        )
        return await self._track_repo.save(track)

    def _artist_to_subsonic(self, artist: Artist) -> SubsonicArtist:
        return SubsonicArtist(
            id=str(artist.id),
            name=artist.name,
            coverArt=str(artist.id) if artist.picture_url else None,
        )

    def _album_to_subsonic(self, album: Album) -> SubsonicAlbum:
        return SubsonicAlbum(
            id=str(album.id),
            name=album.title,
            artistId=str(album.artist_id),
            coverArt=str(album.id) if album.cover_url else None,
            year=album.year,
        )

    def _track_to_subsonic(self, track: Track) -> SubsonicChild:
        return SubsonicChild(
            id=str(track.id),
            title=track.title,
            artistId=str(track.artist_id),
            albumId=str(track.album_id) if track.album_id else None,
            duration=track.duration,
            track=track.track_number,
        )

    async def get_artist_by_id(self, artist_id: int) -> Artist | None:
        return await self._artist_repo.get_by_id(artist_id)

    async def get_album_by_id(self, album_id: int) -> Album | None:
        return await self._album_repo.get_by_id(album_id)

    async def get_track_by_id(self, track_id: int) -> Track | None:
        return await self._track_repo.get_by_id(track_id)

    def artist_to_subsonic(self, artist: Artist) -> SubsonicArtist:
        return self._artist_to_subsonic(artist)

    def album_to_subsonic(self, album: Album) -> SubsonicAlbum:
        return self._album_to_subsonic(album)

    def track_to_subsonic(self, track: Track) -> SubsonicChild:
        return self._track_to_subsonic(track)
