from dataclasses import dataclass

@dataclass
class SlskdConfig:
    api_url: str = "http://localhost:5030"
    api_key: str = ""
    downloads_dir: str = "var/slskd/downloads"
    search_timeout: int = 10
    download_timeout: int = 60
