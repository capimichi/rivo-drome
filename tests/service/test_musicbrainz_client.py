import pytest
import httpx
from unittest.mock import MagicMock
from rivo_drome.config.musicbrainz_config import MusicBrainzConfig
from rivo_drome.client.musicbrainz_client import MusicBrainzClient

@pytest.mark.asyncio
async def test_get_alternative_albums_success(monkeypatch):
    config = MusicBrainzConfig(user_agent="TestAgent/1.0.0")
    client = MusicBrainzClient(config)
    
    mock_resp_json = {
        "recordings": [
            {
                "title": "Bohemian Rhapsody",
                "releases": [
                    {"title": "A Night at the Opera"},
                    {"title": "Greatest Hits"},
                ]
            },
            {
                "title": "Bohemian Rhapsody (Live)",
                "releases": [
                    {"title": "Live at Wembley '86"},
                    {"title": "A Night at the Opera"}  # Duplicate, should be ignored
                ]
            }
        ]
    }
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_json
    mock_response.raise_for_status = MagicMock()
    
    async def mock_get(*args, **kwargs):
        return mock_response
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    
    albums = await client.get_alternative_albums("Queen", "Bohemian Rhapsody")
    assert len(albums) == 3
    assert albums == ["A Night at the Opera", "Greatest Hits", "Live at Wembley '86"]
