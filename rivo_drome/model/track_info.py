from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TrackInfo:
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None
    track_number: Optional[int] = None
    alternative_albums: List[str] = field(default_factory=list)


