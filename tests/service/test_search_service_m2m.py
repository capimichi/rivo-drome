import pytest
from unittest.mock import MagicMock, AsyncMock
from rivo_drome.service.search_service import SearchService
from rivo_drome.entity.track import Track
from rivo_drome.entity.album import Album
from rivo_drome.client.deezer_client import DeezerClient
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.album_repository import AlbumRepository
from rivo_drome.repository.track_repository import TrackRepository

@pytest.mark.asyncio
async def test_track_to_subsonic_m2m():
    deezer_client = MagicMock(spec=DeezerClient)
    artist_repo = MagicMock(spec=ArtistRepository)
    album_repo = MagicMock(spec=AlbumRepository)
    track_repo = MagicMock(spec=TrackRepository)
    
    service = SearchService(deezer_client, artist_repo, album_repo, track_repo)
    
    album = Album(id=42, title="Test Album")
    track = Track(id=1, title="Test Song", artist_id=10, duration=180, track_number=5)
    track.albums.append(album)
    
    subsonic_child = service.track_to_subsonic(track)
    assert subsonic_child.albumId == "42"
    assert subsonic_child.coverArt == "al-42"
