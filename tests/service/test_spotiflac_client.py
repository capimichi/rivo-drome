import pytest
import respx
from httpx import Response
from rivo_drome.client.spotiflac_client import SpotiFlacClient
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

@pytest.mark.asyncio
@respx.mock
async def test_spotiflac_client_download_success():
    config = SpotiFlacConfig(base_url="http://test-server")
    client = SpotiFlacClient(config)
    
    mock_payload = {
        "url": "https://open.qobuz.com/track/123",
        "service": "qobuz",
        "quality": "6",
        "output_dir": "/tmp/downloads"
    }
    
    mock_response = {
        "status": "completed",
        "files": ["/tmp/downloads/Queen - Bohemian Rhapsody.flac"]
    }
    
    respx.post("http://test-server/api/download/sync", json=mock_payload).mock(
        return_value=Response(200, json=mock_response)
    )
    
    file_path = await client.download_sync(
        url="https://open.qobuz.com/track/123",
        service="qobuz",
        quality="6",
        output_dir="/tmp/downloads"
    )
    
    assert file_path == "/tmp/downloads/Queen - Bohemian Rhapsody.flac"

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
