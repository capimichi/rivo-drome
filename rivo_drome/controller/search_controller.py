from fastapi import APIRouter, Query, HTTPException
from injector import inject
from starlette.responses import JSONResponse

from rivo_drome.model.subsonic_schema import SubsonicResponse, SubsonicEnvelope, SubsonicArtist, SubsonicAlbum
from rivo_drome.service.search_service import SearchService


class SearchController:
    @inject
    def __init__(self, search_service: SearchService):
        self._search_service = search_service
        self.router = APIRouter()
        self.router.add_api_route("/rest/search2.view", self.search, methods=["GET"])
        self.router.add_api_route("/rest/search3.view", self.search, methods=["GET"])
        self.router.add_api_route("/rest/getArtist.view", self.get_artist, methods=["GET"])
        self.router.add_api_route("/rest/getAlbum.view", self.get_album, methods=["GET"])
        self.router.add_api_route("/rest/getSong.view", self.get_song, methods=["GET"])

    async def search(
        self,
        query: str = Query(""),
        artistCount: int = Query(20, alias="artistCount"),
        albumCount: int = Query(20, alias="albumCount"),
        songCount: int = Query(20, alias="songCount"),
    ):
        result = await self._search_service.search(query, artistCount, albumCount, songCount)
        envelope = SubsonicEnvelope(
            subsonic_response=SubsonicResponse(searchResult3=result)
        )
        return JSONResponse(content=envelope.model_dump(by_alias=True))

    async def get_artist(self, id: str = Query(...)):
        artist = await self._search_service.get_artist_by_id(int(id))
        if artist is None:
            raise HTTPException(status_code=404, detail="Artist not found")
        subsonic_artist = self._search_service.artist_to_subsonic(artist)
        envelope = SubsonicEnvelope(
            subsonic_response=SubsonicResponse(artist=subsonic_artist)
        )
        return JSONResponse(content=envelope.model_dump(by_alias=True))

    async def get_album(self, id: str = Query(...)):
        album = await self._search_service.get_album_by_id(int(id))
        if album is None:
            raise HTTPException(status_code=404, detail="Album not found")
        subsonic_album = self._search_service.album_to_subsonic(album)
        envelope = SubsonicEnvelope(
            subsonic_response=SubsonicResponse(album=subsonic_album)
        )
        return JSONResponse(content=envelope.model_dump(by_alias=True))

    async def get_song(self, id: str = Query(...)):
        track = await self._search_service.get_track_by_id(int(id))
        if track is None:
            raise HTTPException(status_code=404, detail="Song not found")
        subsonic_track = self._search_service.track_to_subsonic(track)
        envelope = SubsonicEnvelope(
            subsonic_response=SubsonicResponse(song=subsonic_track)
        )
        return JSONResponse(content=envelope.model_dump(by_alias=True))
