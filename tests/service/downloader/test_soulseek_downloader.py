import pytest
import os
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from rivo_drome.config.slskd_config import SlskdConfig
from rivo_drome.client.slskd_client import SlskdClient
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.soulseek_downloader import SoulseekDownloader

@pytest.mark.asyncio
async def test_do_download_success(tmp_path):
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    
    # Mock the actual file written on disk
    mock_slskd_file_relative = "artist/album/song.flac"
    full_mock_file = downloads_dir / mock_slskd_file_relative
    full_mock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(full_mock_file, "w") as f:
        f.write("mock binary music data")
        
    config = SlskdConfig(downloads_dir=str(downloads_dir), search_timeout=5, download_timeout=10)
    client = MagicMock(spec=SlskdClient)
    client.search = AsyncMock(return_value="search_id_123")
    
    # Mock search responses (FLAC and MP3)
    mock_responses = [
        {
            "username": "user1",
            "files": [
                {
                    "filename": "artist\\album\\song.flac",
                    "size": 100,
                    "bitRate": 1411,
                    "extension": "flac"
                },
                {
                    "filename": "artist\\album\\song.mp3",
                    "size": 50,
                    "bitRate": 320,
                    "extension": "mp3"
                }
            ]
        }
    ]
    client.get_search_responses = AsyncMock(return_value=mock_responses)
    client.get_search_status = AsyncMock(return_value={"isComplete": True})
    client.enqueue_download = AsyncMock(return_value={"enqueued": [{"id": "transfer_id_456", "filename": "artist\\album\\song.flac"}]})
    
    # Mock active downloads list: first Queued, then Succeeded
    client.get_downloads = AsyncMock()
    client.get_downloads.side_effect = [
        [{"username": "user1", "filename": "artist\\album\\song.flac", "id": "transfer_id_456", "state": "Queued"}],
        [{"username": "user1", "filename": "artist\\album\\song.flac", "id": "transfer_id_456", "state": "Succeeded"}]
    ]
    client.delete_search = AsyncMock()
    client.delete_download = AsyncMock()

    downloader = SoulseekDownloader(client, config)
    track_info = TrackInfo(title="song", artist="artist", album="album")
    dest_path = str(tmp_path / "final_song.flac")

    with patch("asyncio.sleep", AsyncMock()):
        result = await downloader._do_download(track_info, dest_path)

    assert result == dest_path
    assert os.path.exists(dest_path)
    client.enqueue_download.assert_called_once_with("user1", "artist\\album\\song.flac", 100)
    client.delete_search.assert_called_once_with("search_id_123")
    client.delete_download.assert_called_once_with("user1", "transfer_id_456")
