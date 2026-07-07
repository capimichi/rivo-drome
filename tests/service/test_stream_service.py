import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rivo_drome.service.stream_service import StreamService
from rivo_drome.entity.track import Track
from rivo_drome.entity.artist import Artist
from rivo_drome.entity.album import Album
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.repository.track_repository import TrackRepository
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.album_repository import AlbumRepository
from rivo_drome.service.downloader.base_downloader import BaseDownloader
from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger
from rivo_drome.client.navidrome_client import NavidromeClient
from rivo_drome.config.navidrome_config import NavidromeConfig

@pytest.fixture
def stream_service_setup():
    track_repo = MagicMock(spec=TrackRepository)
    artist_repo = MagicMock(spec=ArtistRepository)
    album_repo = MagicMock(spec=AlbumRepository)
    downloader_chain = MagicMock(spec=BaseDownloader)
    logger = MagicMock(spec=TorrentDownloaderLogger)
    navidrome_client = MagicMock(spec=NavidromeClient)
    navidrome_config = NavidromeConfig(url="http://localhost:4533", music_dir="/music")

    svc = StreamService(
        track_repository=track_repo,
        artist_repository=artist_repo,
        album_repository=album_repo,
        downloader_chain=downloader_chain,
        download_dir="/downloads",
        torrent_downloader_logger=logger,
        navidrome_client=navidrome_client,
        navidrome_config=navidrome_config,
    )
    return svc, track_repo, artist_repo, album_repo, downloader_chain, navidrome_client

@pytest.mark.asyncio
async def test_stream_or_download_existing_on_navidrome(stream_service_setup):
    svc, track_repo, artist_repo, album_repo, downloader_chain, navidrome_client = stream_service_setup

    track = Track(id=1, title="Bohemian Rhapsody", artist_id=2, album_id=3, track_number=11)
    artist = Artist(id=2, name="Queen")
    
    track_repo.get_by_id = AsyncMock(return_value=track)
    artist_repo.get_by_id = AsyncMock(return_value=artist)
    album_repo.get_by_id = AsyncMock(return_value=None)
    
    # Simulate track exists on Navidrome
    navidrome_client.search_track = AsyncMock(return_value="Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3")

    with patch("os.path.exists", return_value=True):
        res = await svc.stream_or_download(1)
        assert res == "/music/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
        assert track.local_path == "/music/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
        assert track.status == "downloaded"
        track_repo.save.assert_called_once_with(track)

@pytest.mark.asyncio
async def test_stream_or_download_trigger_download_and_rescan(stream_service_setup):
    svc, track_repo, artist_repo, album_repo, downloader_chain, navidrome_client = stream_service_setup

    track = Track(id=1, title="Bohemian Rhapsody", artist_id=2, album_id=3, track_number=11)
    artist = Artist(id=2, name="Queen")
    album = Album(id=3, title="A Night at the Opera")
    
    track_repo.get_by_id = AsyncMock(return_value=track)
    artist_repo.get_by_id = AsyncMock(return_value=artist)
    album_repo.get_by_id = AsyncMock(return_value=album)
    
    # Simulate track does NOT exist on Navidrome
    navidrome_client.search_track = AsyncMock(return_value=None)
    
    # Mock downloader download return path
    downloader_chain.download = AsyncMock(return_value="/downloads/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3")
    navidrome_client.trigger_rescan = AsyncMock()

    with patch("os.path.exists", return_value=False), patch("os.makedirs"):
        res = await svc.stream_or_download(1)
        assert res == "/downloads/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
        assert track.local_path == "/downloads/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
        assert track.status == "downloaded"
        track_repo.save.assert_called_once_with(track)
        navidrome_client.trigger_rescan.assert_called_once()
