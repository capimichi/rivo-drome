import httpx
from typing import List
from injector import inject
from rivo_drome.config.musicbrainz_config import MusicBrainzConfig


class MusicBrainzClient:
    @inject
    def __init__(self, config: MusicBrainzConfig):
        self._user_agent = config.user_agent

    async def get_alternative_albums(self, artist: str, title: str) -> List[str]:
        headers = {"User-Agent": self._user_agent}
        query = f'recording:"{title}" AND artist:"{artist}"'
        params = {"query": query, "fmt": "json"}
        url = "https://musicbrainz.org/ws/2/recording"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except Exception:
                return []
                
        recordings = data.get("recordings", [])
        album_titles = []
        seen = set()
        for recording in recordings:
            for release in recording.get("releases", []):
                rel_title = release.get("title")
                if rel_title and rel_title.lower().strip() not in seen:
                    seen.add(rel_title.lower().strip())
                    album_titles.append(rel_title)
                    if len(album_titles) == 5:
                        return album_titles
        return album_titles
