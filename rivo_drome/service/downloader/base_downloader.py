import logging
from abc import ABC, abstractmethod
from typing import Optional

from rivo_drome.model.track_info import TrackInfo

class BaseDownloader(ABC):
    def __init__(self):
        self._next: Optional[BaseDownloader] = None
        self._logger = None

    def set_next(self, downloader: "BaseDownloader") -> "BaseDownloader":
        self._next = downloader
        return downloader

    async def download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        downloader_name = self.__class__.__name__
        
        # Get active logger (either injected on subclass, or dummy/default logger)
        logger_obj = self._logger.logger if (hasattr(self, "_logger") and self._logger) else logging.getLogger("BaseDownloader")
        
        logger_obj.info("%s: starting download attempt for '%s - %s'", downloader_name, track_info.artist, track_info.title)
        
        result = await self._do_download(track_info, dest_path)
        if result:
            logger_obj.info("%s: download succeeded!", downloader_name)
            return result
            
        logger_obj.warning("%s: download failed or skipped.", downloader_name)
        if self._next is not None:
            logger_obj.info("BaseDownloader: transitioning to next downloader in chain: %s", self._next.__class__.__name__)
            return await self._next.download(track_info, dest_path)
            
        return None

    @abstractmethod
    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        pass
