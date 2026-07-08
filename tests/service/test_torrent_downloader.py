import pytest
from unittest.mock import MagicMock, AsyncMock
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.torrent_downloader import TorrentDownloader
from rivo_drome.client.jackett_client import JackettClient
from rivo_drome.client.torrserver_client import TorrServerClient
from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger

@pytest.mark.asyncio
async def test_torrent_downloader_queries_sequence():
    jackett_client = MagicMock(spec=JackettClient)
    torrserver_client = MagicMock(spec=TorrServerClient)
    logger = MagicMock(spec=TorrentDownloaderLogger)
    
    jackett_client.search = AsyncMock(return_value=[])
    
    downloader = TorrentDownloader(jackett_client, torrserver_client, logger)
    
    track_info = TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        alternative_albums=["Greatest Hits", "Live Wembley"]
    )
    
    await downloader._do_download(track_info, "/tmp/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3")
    
    assert jackett_client.search.call_count == 4
    jackett_client.search.assert_any_call("Queen A Night at the Opera")
    jackett_client.search.assert_any_call("Queen Greatest Hits")
    jackett_client.search.assert_any_call("Queen Live Wembley")
    jackett_client.search.assert_any_call("Queen - Bohemian Rhapsody")
