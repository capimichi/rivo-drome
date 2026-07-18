import logging
import asyncio
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

class DeezerClient:
    BASE_URL = "https://api.deezer.com"

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=45.0)

    async def _get_with_retry(self, url: str, params: Optional[Dict] = None) -> httpx.Response:
        retries = 3
        for attempt in range(retries):
            try:
                response = await self._client.get(url, params=params)
                response.raise_for_status()
                return response
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as e:
                if attempt == retries - 1:
                    raise
                logger.warning("DeezerClient request failed (attempt %d/%d): %s. Retrying...", attempt + 1, retries, e)
                await asyncio.sleep(2)
        # Fallback to satisfy return type check, though raise will prevent reaching here
        raise httpx.NetworkError("Failed after retries")

    async def search(self, query: str, limit: int = 25) -> Dict[str, Any]:
        response = await self._get_with_retry(
            f"{self.BASE_URL}/search",
            params={"q": query, "limit": limit},
        )
        return response.json()

    async def search_artist(self, query: str, limit: int = 10) -> Dict[str, Any]:
        response = await self._get_with_retry(
            f"{self.BASE_URL}/search/artist",
            params={"q": query, "limit": limit},
        )
        return response.json()

    async def search_album(self, query: str, limit: int = 10) -> Dict[str, Any]:
        response = await self._get_with_retry(
            f"{self.BASE_URL}/search/album",
            params={"q": query, "limit": limit},
        )
        return response.json()

    async def search_track(self, query: str, limit: int = 10) -> Dict[str, Any]:
        response = await self._get_with_retry(
            f"{self.BASE_URL}/search/track",
            params={"q": query, "limit": limit},
        )
        return response.json()

    async def get_artist(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self._get_with_retry(f"{self.BASE_URL}/artist/{deezer_id}")
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_album(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self._get_with_retry(f"{self.BASE_URL}/album/{deezer_id}")
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_track(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self._get_with_retry(f"{self.BASE_URL}/track/{deezer_id}")
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
