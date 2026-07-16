from dataclasses import dataclass
from typing import Optional


@dataclass
class SpotiFlacConfig:
    base_url: str = "http://localhost:8080"
    username: Optional[str] = None
    password: Optional[str] = None
