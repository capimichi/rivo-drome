from abc import ABC, abstractmethod
from typing import Optional

from rivo_drome.model.track_info import TrackInfo


class BaseDownloader(ABC):
    def __init__(self):
        self._next: Optional[BaseDownloader] = None

    def set_next(self, downloader: "BaseDownloader") -> "BaseDownloader":
        self._next = downloader
        return downloader

    async def download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        result = await self._do_download(track_info, dest_path)
        if result is None and self._next is not None:
            return await self._next.download(track_info, dest_path)
        return result

    @abstractmethod
    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        pass
