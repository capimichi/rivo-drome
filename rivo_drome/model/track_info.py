from dataclasses import dataclass
from typing import Optional


@dataclass
class TrackInfo:
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None
