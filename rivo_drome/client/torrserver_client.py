from typing import Optional, Dict, Any, List

import httpx
from injector import inject

from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger


class TorrServerClient:
    @inject
    def __init__(self, torrserver_url: str, torrent_downloader_logger: TorrentDownloaderLogger):
        self._base_url = torrserver_url.rstrip("/")
        self._logger = torrent_downloader_logger

    async def add_torrent(self, magnet: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/torrents",
                json={"action": "add", "link": magnet, "save_to_db": True},
            )
            if response.status_code == 422:
                self._logger.log_torrent_add(magnet, success=False)
                return None
            response.raise_for_status()
            data = response.json()
            info_hash = data.get("hash")
            self._logger.log_torrent_add(magnet, success=True, info_hash=info_hash)
            return data

    async def get_torrent_info(self, info_hash: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/torrents",
                json={"action": "get", "hash": info_hash},
            )
            if response.status_code == 404:
                self._logger.log_torrent_info(info_hash, file_count=0, has_audio=False)
                return None
            response.raise_for_status()
            data = response.json()

            # TorrServer packages file list under the "data" field as a JSON string
            files = []
            if "data" in data and isinstance(data["data"], str):
                import json
                try:
                    inner_data = json.loads(data["data"])
                    files = inner_data.get("files", [])
                except Exception:
                    pass
            
            if not files:
                files = data.get("files") or data.get("file_stats") or []

            # Normalize to key 'files' so consumers can read it directly
            data["files"] = files

            has_audio = any(
                f.get("path", f.get("name", "")).lower().endswith(
                    (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma")
                )
                for f in files
            )
            self._logger.log_torrent_info(info_hash, file_count=len(files), has_audio=has_audio)
            return data


    async def get_torrents(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/torrents",
                json={"action": "list"},
            )
            response.raise_for_status()
            data = response.json()
            self._logger.logger.info("List torrents count=%d", len(data))
            return data

    def get_file_stream_url(self, info_hash: str, file_index: int) -> str:
        url = f"{self._base_url}/stream?link={info_hash}&index={file_index}&play"
        self._logger.log_stream_url(info_hash, file_index, url)
        return url


