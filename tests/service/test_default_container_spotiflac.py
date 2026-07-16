import os
from unittest.mock import patch
from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.config.spotiflac_config import SpotiFlacConfig
from rivo_drome.service.downloader.spotiflac_downloader import SpotiFlacDownloader

def test_default_container_wires_spotiflac():
    env = {
        "DOWNLOADER_CHAIN": "spotiflac,youtube",
        "SPOTIFLAC_API_URL": "http://my-custom-spotiflac:1234",
        "SPOTIFLAC_USERNAME": "admin",
        "SPOTIFLAC_PASSWORD": "pwd"
    }
    with patch.dict(os.environ, env):
        # Reset container instance for testing
        DefaultContainer.instance = None
        container = DefaultContainer.getInstance()
        
        config = container.get(SpotiFlacConfig)
        assert config.base_url == "http://my-custom-spotiflac:1234"
        assert config.username == "admin"
        assert config.password == "pwd"
        
        # Test downloader resolution
        downloader = container.get(SpotiFlacDownloader)
        assert downloader is not None
