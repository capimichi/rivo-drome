import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OdesliClient:
    API_URL = "https://api.song.link/v1-alpha.1/links"

    async def get_track_links(self, deezer_id: int) -> Dict[str, Optional[str]]:
        deezer_url = f"https://www.deezer.com/track/{deezer_id}"
        params = {
            "url": deezer_url,
            "userCountry": "IT"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                links = {}
                links_by_platform = data.get("linksByPlatform", {})
                for platform in ["qobuz", "tidal", "amazonMusic"]:
                    if platform in links_by_platform:
                        links[platform] = links_by_platform[platform].get("url")
                return links
            except Exception as e:
                logger.error("Odesli link resolution failed for deezer_id %s: %s", deezer_id, e)
                return {}
