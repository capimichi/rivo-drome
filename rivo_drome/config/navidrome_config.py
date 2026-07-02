from dataclasses import dataclass


@dataclass
class NavidromeConfig:
    url: str = "http://localhost:4533"
    music_dir: str = ""
