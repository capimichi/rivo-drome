from rivo_drome.config.slskd_config import SlskdConfig

def test_slskd_config_defaults():
    config = SlskdConfig()
    assert config.api_url == "http://localhost:5030"
    assert config.api_key == ""
    assert config.downloads_dir == "var/slskd/downloads"
    assert config.search_timeout == 10
    assert config.download_timeout == 60

def test_slskd_config_custom():
    config = SlskdConfig(
        api_url="http://slskd.local:5030",
        api_key="secret",
        downloads_dir="/path/to/downloads",
        search_timeout=5,
        download_timeout=30
    )
    assert config.api_url == "http://slskd.local:5030"
    assert config.api_key == "secret"
    assert config.downloads_dir == "/path/to/downloads"
    assert config.search_timeout == 5
    assert config.download_timeout == 30
