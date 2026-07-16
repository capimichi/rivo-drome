from rivo_drome.config.spotiflac_config import SpotiFlacConfig

def test_spotiflac_config_defaults():
    config = SpotiFlacConfig()
    assert config.base_url == "http://localhost:8080"
    assert config.username is None
    assert config.password is None

def test_spotiflac_config_custom():
    config = SpotiFlacConfig(base_url="http://my-spotiflac:9000", username="admin", password="password123")
    assert config.base_url == "http://my-spotiflac:9000"
    assert config.username == "admin"
    assert config.password == "password123"
