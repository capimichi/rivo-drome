import pytest
import respx
from httpx import Response
from rivo_drome.client.spotiflac_client import SpotiFlacClient
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

import os

@pytest.mark.asyncio
@respx.mock
async def test_spotiflac_client_download_success(tmp_path):
    config = SpotiFlacConfig(base_url="http://test-server")
    client = SpotiFlacClient(config)
    
    mock_payload = {
        "url": "https://open.qobuz.com/track/123",
        "service": "qobuz",
        "quality": "6",
        "output_dir": "./downloads"
    }
    
    mock_response = {
        "status": "completed",
        "files": ["downloads/Queen - Bohemian Rhapsody.flac"]
    }
    
    respx.post("http://test-server/api/download/sync", json=mock_payload).mock(
        return_value=Response(200, json=mock_response)
    )
    
    respx.get("http://test-server/downloads/Queen%20-%20Bohemian%20Rhapsody.flac").mock(
        return_value=Response(200, content=b"audio data content")
    )
    
    output_dir = str(tmp_path / "downloads")
    file_path = await client.download_sync(
        url="https://open.qobuz.com/track/123",
        service="qobuz",
        quality="6",
        output_dir=output_dir
    )
    
    expected_file_path = os.path.join(output_dir, "Queen - Bohemian Rhapsody.flac")
    assert file_path == expected_file_path
    assert os.path.exists(expected_file_path)
    with open(expected_file_path, "rb") as f:
        assert f.read() == b"audio data content"


@pytest.mark.asyncio
@respx.mock
async def test_spotiflac_client_download_failure():
    config = SpotiFlacConfig(base_url="http://test-server")
    client = SpotiFlacClient(config)
    
    respx.post("http://test-server/api/download/sync").mock(
        return_value=Response(500)
    )
    
    file_path = await client.download_sync(
        url="https://open.qobuz.com/track/123",
        service="qobuz",
        quality="6",
        output_dir="/tmp/downloads"
    )
    
    assert file_path is None
