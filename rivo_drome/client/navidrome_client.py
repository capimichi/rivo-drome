import httpx
import re
from typing import Optional
from injector import inject
from rivo_drome.config.navidrome_config import NavidromeConfig
from rivo_drome.service.navidrome_proxy_service import NavidromeProxyService

class NavidromeClient:
    @inject
    def __init__(self, config: NavidromeConfig, proxy_service: NavidromeProxyService):
        self.navidrome_url = config.url.rstrip("/")
        self.proxy_service = proxy_service

    async def search_track(self, artist: str, title: str) -> Optional[str]:
        creds = self.proxy_service._last_credentials
        if not creds:
            return None

        params = creds.copy()
        params["query"] = f"{artist} {title}"
        params["songCount"] = 50
        params["f"] = "json"

        url = f"{self.navidrome_url}/rest/search3.view"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception:
                return None

        subsonic_resp = data.get("subsonic-response", {})
        if subsonic_resp.get("status") != "ok":
            return None

        songs = subsonic_resp.get("searchResult3", {}).get("song", [])
        if not songs:
            return None

        def normalize(s: str) -> str:
            return re.sub(r'[^a-zA-Z0-9]', '', s).lower() if s else ""

        norm_artist = normalize(artist)
        norm_title = normalize(title)

        for song in songs:
            song_artist = normalize(song.get("artist", ""))
            song_title = normalize(song.get("title", ""))
            if song_artist == norm_artist and song_title == norm_title:
                path = song.get("path")
                if path:
                    return path
        return None

    async def trigger_rescan(self) -> bool:
        creds = self.proxy_service._last_credentials
        if not creds:
            return False

        params = creds.copy()
        params["f"] = "json"
        url = f"{self.navidrome_url}/rest/startScan.view"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                subsonic_resp = data.get("subsonic-response", {})
                return subsonic_resp.get("status") == "ok"
            except Exception:
                return False
