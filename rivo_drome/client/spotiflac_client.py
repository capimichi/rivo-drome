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
            "output_dir": "./downloads"
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
                    internal_file_path = files[0]
                    import os
                    filename = os.path.basename(internal_file_path)
                    
                    from urllib.parse import quote
                    encoded_filename = quote(filename)
                    download_url = f"{self._base_url}/downloads/{encoded_filename}"
                    
                    os.makedirs(output_dir, exist_ok=True)
                    local_dest_path = os.path.join(output_dir, filename)
                    
                    logger.info("SpotiFlacClient: downloading file from HTTP endpoint: %s", download_url)
                    async with client.stream("GET", download_url, auth=auth) as response_stream:
                        response_stream.raise_for_status()
                        with open(local_dest_path, "wb") as f:
                            async for chunk in response_stream.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                                
                    logger.info("SpotiFlacClient: successfully downloaded to local path: %s", local_dest_path)
                    return local_dest_path
                    
                return None
            except Exception as e:
                logger.error("SpotiFLAC REST API download request failed for url %s: %s", url, e)
                return None

