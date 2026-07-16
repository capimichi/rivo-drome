import logging
import httpx
from typing import Optional
from injector import inject
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

logger = logging.getLogger(__name__)


class SpotiFlacClient:
    @inject
    def __init__(self, config: SpotiFlacConfig):
        self._base_url = config.base_url.rstrip("/")
        self._username = config.username
        self._password = config.password

    async def download_sync(self, url: str, service: str, quality: str, output_dir: str) -> Optional[str]:
        target_url = f"{self._base_url}/api/download/sync"
        payload = {
            "url": url,
            "service": service,
            "quality": quality,
            "output_dir": output_dir
        }
        
        auth = None
        if self._username and self._password:
            auth = (self._username, self._password)

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(target_url, json=payload, auth=auth)
                response.raise_for_status()
                data = response.json()
                
                files = data.get("files", [])
                if files and data.get("status") == "completed":
                    return files[0]
                return None
            except Exception as e:
                logger.error("SpotiFLAC REST API download request failed for url %s: %s", url, e)
                return None
