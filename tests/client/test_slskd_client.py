import pytest
import httpx
from unittest.mock import MagicMock
from rivo_drome.config.slskd_config import SlskdConfig
from rivo_drome.client.slskd_client import SlskdClient

@pytest.fixture
def config():
    return SlskdConfig(api_url="http://localhost:5030", api_key="test_key")

@pytest.fixture
def client(config):
    return SlskdClient(config)

@pytest.mark.asyncio
async def test_search(client, monkeypatch):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "search-uuid-123"}
    mock_response.raise_for_status = MagicMock()

    async def mock_post(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    search_id = await client.search("Queen - Bohemian Rhapsody")
    assert search_id == "search-uuid-123"

@pytest.mark.asyncio
async def test_get_search_responses(client, monkeypatch):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [{"username": "peer1", "files": []}]
    mock_response.raise_for_status = MagicMock()

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    responses = await client.get_search_responses("search-uuid-123")
    assert len(responses) == 1
    assert responses[0]["username"] == "peer1"
