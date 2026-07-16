import pytest
import respx
from httpx import Response
from rivo_drome.client.odesli_client import OdesliClient

@pytest.mark.asyncio
@respx.mock
async def test_odesli_client_success():
    deezer_id = 12345
    target_url = f"https://api.song.link/v1-alpha.1/links?url=https://www.deezer.com/track/{deezer_id}&userCountry=IT"
    
    mock_response = {
        "linksByPlatform": {
            "qobuz": {"url": "https://open.qobuz.com/track/qobuz_123"},
            "tidal": {"url": "https://tidal.com/track/tidal_123"},
            "amazonMusic": {"url": "https://music.amazon.com/tracks/amazon_123"}
        }
    }
    respx.get(target_url).mock(return_value=Response(200, json=mock_response))
    
    client = OdesliClient()
    links = await client.get_track_links(deezer_id)
    assert links["qobuz"] == "https://open.qobuz.com/track/qobuz_123"
    assert links["tidal"] == "https://tidal.com/track/tidal_123"
    assert links["amazonMusic"] == "https://music.amazon.com/tracks/amazon_123"

@pytest.mark.asyncio
@respx.mock
async def test_odesli_client_failure():
    deezer_id = 12345
    target_url = f"https://api.song.link/v1-alpha.1/links?url=https://www.deezer.com/track/{deezer_id}&userCountry=IT"
    respx.get(target_url).mock(return_value=Response(500))
    
    client = OdesliClient()
    links = await client.get_track_links(deezer_id)
    assert links == {}
