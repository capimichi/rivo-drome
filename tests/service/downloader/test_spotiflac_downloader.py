import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.spotiflac_downloader import SpotiFlacDownloader
from rivo_drome.client.odesli_client import OdesliClient
from rivo_drome.client.spotiflac_client import SpotiFlacClient

@pytest.mark.asyncio
async def test_spotiflac_downloader_success(tmp_path):
    odesli_client = MagicMock(spec=OdesliClient)
    spotiflac_client = MagicMock(spec=SpotiFlacClient)
    
    track_info = TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        deezer_id=12345
    )
    
    mock_links = {
        "qobuz": "https://open.qobuz.com/track/qobuz_123",
        "amazonMusic": "https://music.amazon.com/tracks/amazon_123",
        "tidal": "https://tidal.com/track/tidal_123"
    }
    odesli_client.get_track_links = AsyncMock(return_value=mock_links)
    
    # Mocking that Qobuz fails but Amazon succeeds
    spotiflac_client.download_sync = AsyncMock()
    
    # We must mock file creation on success
    temp_downloaded_file = tmp_path / "downloads" / "Queen - Bohemian Rhapsody.flac"
    
    def side_effect(url, service, quality, output_dir, **kwargs):
        if service == "qobuz":
            return None
        elif service == "amazon":
            os.makedirs(os.path.dirname(temp_downloaded_file), exist_ok=True)
            with open(temp_downloaded_file, "w") as f:
                f.write("audio content")
            return str(temp_downloaded_file)
        return None
        
    spotiflac_client.download_sync.side_effect = side_effect
    
    downloader = SpotiFlacDownloader(odesli_client, spotiflac_client)
    
    dest_path = str(tmp_path / "music" / "Queen" / "Bohemian Rhapsody.mp3")
    
    result = await downloader._do_download(track_info, dest_path)
    
    assert result == dest_path.replace(".mp3", ".flac")
    assert os.path.exists(dest_path.replace(".mp3", ".flac"))
    
    # Ensure Qobuz was tried first, then Amazon (which succeeded), and Tidal was not tried
    assert spotiflac_client.download_sync.call_count == 2
    spotiflac_client.download_sync.assert_any_call(
        url="https://open.qobuz.com/track/qobuz_123",
        service="qobuz",
        quality="6",
        output_dir=os.path.dirname(dest_path),
        track_name="Bohemian Rhapsody",
        artist_name="Queen",
        album_name=None
    )
    spotiflac_client.download_sync.assert_any_call(
        url="https://music.amazon.com/tracks/amazon_123",
        service="amazon",
        quality="",
        output_dir=os.path.dirname(dest_path),
        track_name="Bohemian Rhapsody",
        artist_name="Queen",
        album_name=None
    )

