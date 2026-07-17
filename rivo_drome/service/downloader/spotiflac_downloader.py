import logging
import os
import shutil
from typing import Optional
from injector import inject

from rivo_drome.client.odesli_client import OdesliClient
from rivo_drome.client.spotiflac_client import SpotiFlacClient
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader

logger = logging.getLogger(__name__)


class SpotiFlacDownloader(BaseDownloader):
    @inject
    def __init__(self, odesli_client: OdesliClient, spotiflac_client: SpotiFlacClient):
        super().__init__()
        self._odesli = odesli_client
        self._spotiflac = spotiflac_client

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        if not track_info.deezer_id:
            logger.warning("SpotiFlacDownloader skipped: no deezer_id provided in track_info")
            return None

        links = await self._odesli.get_track_links(track_info.deezer_id)
        if not links:
            logger.warning("SpotiFlacDownloader: no links resolved via Odesli for deezer_id %s", track_info.deezer_id)
            return None

        # Try services in order: Qobuz -> Amazon -> Tidal
        # Platform key on Odesli mapped to (Service payload key on SpotiFLAC, Quality code)
        services_to_try = [
            ("qobuz", "qobuz", "6"),
            ("amazonMusic", "amazon", ""),
            ("tidal", "tidal", "LOSSLESS")
        ]

        output_dir = os.path.dirname(dest_path)
        os.makedirs(output_dir, exist_ok=True)

        for odesli_key, spotiflac_service, quality in services_to_try:
            url = links.get(odesli_key)
            if not url:
                continue

            logger.info("SpotiFlacDownloader: attempting download from %s using URL: %s", spotiflac_service, url)
            downloaded_file = await self._spotiflac.download_sync(
                url=url,
                service=spotiflac_service,
                quality=quality,
                output_dir=output_dir,
                track_name=track_info.title,
                artist_name=track_info.artist,
                album_name=track_info.album
            )

            if downloaded_file and os.path.exists(downloaded_file):
                logger.info("SpotiFlacDownloader: download succeeded! File: %s", downloaded_file)
                # Keep file extension of downloaded file or rename to dest_path with correct extension
                _, ext = os.path.splitext(downloaded_file)
                final_dest_path = os.path.splitext(dest_path)[0] + ext.lower()
                
                if downloaded_file != final_dest_path:
                    shutil.move(downloaded_file, final_dest_path)
                return final_dest_path

        logger.warning("SpotiFlacDownloader: all service download attempts failed for deezer_id %s", track_info.deezer_id)
        return None
