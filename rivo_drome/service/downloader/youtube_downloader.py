import asyncio
import os
import subprocess
import logging
from typing import Optional

from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader

logger = logging.getLogger(__name__)


class YoutubeDownloader(BaseDownloader):
    def __init__(self):
        super().__init__()

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        query = f"ytsearch:{track_info.artist} - {track_info.title} audio"
        output_template = os.path.splitext(dest_path)[0] + ".%(ext)s"

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "-o", output_template,
                "--max-filesize", "50M",
                "--quiet",
                "--no-warnings",
                query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error("YoutubeDownloader: yt-dlp failed with exit code %d. stderr: %s", proc.returncode, stderr.decode())
                return None

            expected_file = os.path.splitext(dest_path)[0] + ".mp3"
            if os.path.exists(expected_file):
                if expected_file != dest_path:
                    os.rename(expected_file, dest_path)
                return dest_path

            for f in os.listdir(os.path.dirname(dest_path)):
                if f.startswith(os.path.basename(os.path.splitext(dest_path)[0])):
                    full_path = os.path.join(os.path.dirname(dest_path), f)
                    if full_path != dest_path:
                        os.rename(full_path, dest_path)
                    return dest_path

            return None
        except FileNotFoundError:
            logger.error("YoutubeDownloader: yt-dlp binary or dependency not found on system path.")
            return None
