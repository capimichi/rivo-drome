import pytest
from unittest.mock import patch
from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.config.slskd_config import SlskdConfig
from rivo_drome.client.slskd_client import SlskdClient
from rivo_drome.service.downloader.soulseek_downloader import SoulseekDownloader

def test_default_container_slskd_wiring():
    mock_env = {
        "SLSKD_API_URL": "http://test-slskd-url:5030",
        "SLSKD_API_KEY": "test-api-key",
        "SLSKD_DOWNLOADS_DIR": "var/test/downloads",
        "SLSKD_SEARCH_TIMEOUT": "15",
        "SLSKD_DOWNLOAD_TIMEOUT": "90",
        "DOWNLOADER_CHAIN": "soulseek"
    }
    
    with patch.dict("os.environ", mock_env):
        container = DefaultContainer()
        
        # Verify config registration
        config = container.get(SlskdConfig)
        assert config.api_url == "http://test-slskd-url:5030"
        assert config.api_key == "test-api-key"
        assert config.downloads_dir == "var/test/downloads"
        assert config.search_timeout == 15
        assert config.download_timeout == 90
        
        # Verify client and downloader resolution
        client = container.get(SlskdClient)
        assert client is not None
        
        downloader = container.get(SoulseekDownloader)
        assert downloader is not None
