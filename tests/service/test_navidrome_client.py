import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from rivo_drome.config.navidrome_config import NavidromeConfig
from rivo_drome.service.navidrome_proxy_service import NavidromeProxyService
from rivo_drome.client.navidrome_client import NavidromeClient

@pytest.fixture
def navidrome_setup():
    config = NavidromeConfig(url="http://localhost:4533")
    proxy_service = MagicMock(spec=NavidromeProxyService)
    proxy_service._last_credentials = {
        "u": "admin",
        "t": "token",
        "s": "salt",
        "v": "1.16.1",
        "c": "test-client",
        "f": "json",
    }
    client = NavidromeClient(config, proxy_service)
    return client, proxy_service

@pytest.mark.asyncio
async def test_search_track_success(navidrome_setup, monkeypatch):
    client, _ = navidrome_setup

    mock_resp_json = {
        "subsonic-response": {
            "status": "ok",
            "searchResult3": {
                "song": [
                    {
                        "title": "Bohemian Rhapsody",
                        "artist": "Queen",
                        "path": "Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
                    }
                ]
            }
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_json
    mock_response.raise_for_status = MagicMock()

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    path = await client.search_track("Queen", "Bohemian Rhapsody")
    assert path == "Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"

@pytest.mark.asyncio
async def test_trigger_rescan_success(navidrome_setup, monkeypatch):
    client, _ = navidrome_setup

    mock_resp_json = {
        "subsonic-response": {
            "status": "ok"
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_json
    mock_response.raise_for_status = MagicMock()

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    success = await client.trigger_rescan()
    assert success is True
