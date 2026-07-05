from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SubsonicChild(BaseModel):
    id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    artistId: Optional[str] = None
    album: Optional[str] = None
    albumId: Optional[str] = None
    duration: Optional[int] = None
    track: Optional[int] = None
    year: Optional[int] = None
    coverArt: Optional[str] = None
    parent: Optional[str] = None
    contentType: Optional[str] = None
    suffix: Optional[str] = None
    size: Optional[int] = None
    path: Optional[str] = None
    isDir: Optional[bool] = None


class SubsonicArtist(BaseModel):
    id: str
    name: str
    albumCount: Optional[int] = None
    coverArt: Optional[str] = None
    artistImageUrl: Optional[str] = None


class SubsonicAlbum(BaseModel):
    id: str
    name: str
    artist: Optional[str] = None
    artistId: Optional[str] = None
    coverArt: Optional[str] = None
    songCount: Optional[int] = None
    duration: Optional[int] = None
    year: Optional[int] = None
    created: Optional[str] = None


class SearchResult3(BaseModel):
    artist: List[SubsonicArtist] = []
    album: List[SubsonicAlbum] = []
    song: List[SubsonicChild] = []


class SubsonicResponse(BaseModel):
    status: str = "ok"
    version: str = "1.16.1"
    searchResult3: Optional[SearchResult3] = None
    artist: Optional[SubsonicArtist] = None
    album: Optional[SubsonicAlbum] = None
    song: Optional[SubsonicChild] = None


class SubsonicEnvelope(BaseModel):
    subsonic_response: SubsonicResponse

    model_config = {
        "alias_generator": lambda s: s.replace("_", "-"),
        "populate_by_name": True,
    }
