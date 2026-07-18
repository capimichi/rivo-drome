import logging
import httpx
from typing import List, Dict, Optional
from injector import inject
from rivo_drome.config.slskd_config import SlskdConfig

logger = logging.getLogger(__name__)

class SlskdClient:
    @inject
    def __init__(self, config: SlskdConfig):
        self._base_url = config.api_url.rstrip("/")
        self._api_key = config.api_key
        self._headers = {"X-API-Key": self._api_key}

    async def search(self, query: str) -> Optional[str]:
        url = f"{self._base_url}/api/v0/searches"
        payload = {"searchText": query}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self._headers)
                response.raise_for_status()
                data = response.json()
                return data.get("id")
            except Exception as e:
                logger.error("SlskdClient search request failed: %s", e)
                return None

    async def get_search_responses(self, search_id: str) -> List[Dict]:
        url = f"{self._base_url}/api/v0/searches/{search_id}/responses"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("SlskdClient get_search_responses failed: %s", e)
                return []

    async def delete_search(self, search_id: str) -> None:
        url = f"{self._base_url}/api/v0/searches/{search_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.delete(url, headers=self._headers)
                response.raise_for_status()
            except Exception as e:
                logger.warning("SlskdClient delete_search failed: %s", e)

    async def enqueue_download(self, username: str, filename: str, size: int) -> Optional[Dict]:
        url = f"{self._base_url}/api/v0/transfers/downloads/{username}"
        payload = {"filename": filename, "size": size}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self._headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("SlskdClient enqueue_download failed for user %s: %s", username, e)
                return None

    async def get_downloads(self) -> List[Dict]:
        url = f"{self._base_url}/api/v0/transfers/downloads"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("SlskdClient get_downloads failed: %s", e)
                return []

    async def delete_download(self, username: str, id: str) -> None:
        url = f"{self._base_url}/api/v0/transfers/downloads/{username}/{id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.delete(url, headers=self._headers)
                response.raise_for_status()
            except Exception as e:
                logger.warning("SlskdClient delete_download failed for user %s and transfer id %s: %s", username, id, e)
