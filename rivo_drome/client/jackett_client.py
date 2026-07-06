from typing import Optional, List, Dict, Any

import httpx


class JackettClient:
    def __init__(self, jackett_url: str, api_key: str):
        self._base_url = jackett_url.rstrip("/")
        self._api_key = api_key

    async def search(self, query: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base_url}/api/v2.0/indexers/all/results",
                params={"Query": query, "apikey": self._api_key},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("Results", [])

