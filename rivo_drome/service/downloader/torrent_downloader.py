import asyncio
import os
from typing import Optional

import httpx

from rivo_drome.client.jackett_client import JackettClient
from rivo_drome.client.torrserver_client import TorrServerClient
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader


class TorrentDownloader(BaseDownloader):
    AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma"}

    def __init__(self, jackett_client: JackettClient, torrserver_client: TorrServerClient):
        super().__init__()
        self._jackett = jackett_client
        self._torrserver = torrserver_client

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        query = f"{track_info.artist} - {track_info.title}"
        results = await self._jackett.search(query)

        if not results:
            return None

        for result in results[:5]:
            magnet = result.get("Link") or result.get("Magnet")
            if not magnet:
                continue

            torrent_data = await self._torrserver.add_torrent(magnet)
            if torrent_data is None:
                continue

            info_hash = torrent_data.get("hash")
            if not info_hash:
                continue

            await asyncio.sleep(2)

            torrent_info = await self._torrserver.get_torrent_info(info_hash)
            if not torrent_info:
                continue

            files = torrent_info.get("files", [])
            audio_file = self._find_audio_file(files, track_info)
            if audio_file is None:
                continue

            file_index = audio_file.get("id")
            if file_index is None:
                continue

            stream_url = self._torrserver.get_file_stream_url(info_hash, file_index)
            return await self._download_file(stream_url, dest_path)

        return None

    def _find_audio_file(self, files: list, track_info: TrackInfo) -> Optional[dict]:
        for f in files:
            path = f.get("path", f.get("name", ""))
            ext = os.path.splitext(path)[1].lower()
            if ext in self.AUDIO_EXTENSIONS:
                return f
        return None

    async def _download_file(self, url: str, dest_path: str) -> Optional[str]:
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with open(dest_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                    return dest_path
        except Exception:
            return None
