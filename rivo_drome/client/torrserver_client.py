from typing import Optional, Dict, Any, List

import httpx


class TorrServerClient:
    def __init__(self, torrserver_url: str):
        self._base_url = torrserver_url.rstrip("/")

    async def add_torrent(self, magnet: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/torrents/add",
                json={"link": magnet},
            )
            if response.status_code == 422:
                return None
            response.raise_for_status()
            return response.json()

    async def get_torrent_info(self, info_hash: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/torrents/info",
                params={"hash": info_hash},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_torrents(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base_url}/torrents/list")
            response.raise_for_status()
            return response.json()

    def get_file_stream_url(self, info_hash: str, file_index: int) -> str:
        return f"{self._base_url}/stream/{info_hash}/{file_index}"
