from typing import Optional, Dict, Any

import httpx


class DeezerClient:
    BASE_URL = "https://api.deezer.com"

    async def search(self, query: str, limit: int = 25) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def search_artist(self, query: str, limit: int = 10) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/artist",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def search_album(self, query: str, limit: int = 10) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/album",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def search_track(self, query: str, limit: int = 10) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/track",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def get_artist(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/artist/{deezer_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_album(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/album/{deezer_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_track(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/track/{deezer_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
