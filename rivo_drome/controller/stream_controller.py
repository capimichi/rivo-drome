import os

from fastapi import APIRouter, Query, HTTPException
from injector import inject
from starlette.responses import FileResponse

from rivo_drome.service.stream_service import StreamService


class StreamController:
    @inject
    def __init__(self, stream_service: StreamService):
        self._stream_service = stream_service
        self.router = APIRouter()
        self.router.add_api_route("/rest/stream.view", self.stream, methods=["GET"])
        self.router.add_api_route("/rest/download.view", self.download, methods=["GET"])

    async def stream(self, id: str = Query(...)):
        path = await self._stream_service.stream_or_download(int(id))
        if path is None:
            raise HTTPException(status_code=404, detail="Track not found or download failed")
        return FileResponse(
            path=path,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline"},
        )

    async def download(self, id: str = Query(...)):
        path = await self._stream_service.stream_or_download(int(id))
        if path is None:
            raise HTTPException(status_code=404, detail="Track not found or download failed")
        filename = os.path.basename(path)
        return FileResponse(
            path=path,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
