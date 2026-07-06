import os
from typing import Optional

from injector import inject

from rivo_drome.entity.track import Track
from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.track_repository import TrackRepository
from rivo_drome.service.downloader.base_downloader import BaseDownloader


class StreamService:
    @inject
    def __init__(
        self,
        track_repository: TrackRepository,
        artist_repository: ArtistRepository,
        downloader_chain: BaseDownloader,
        download_dir: str,
        torrent_downloader_logger: TorrentDownloaderLogger,
    ):
        self._track_repo = track_repository
        self._artist_repo = artist_repository
        self._downloader = downloader_chain
        self._download_dir = download_dir
        self._logger = torrent_downloader_logger

    async def get_track_path(self, track_id: int) -> Optional[str]:
        track = await self._track_repo.get_by_id(track_id)
        if track is None:
            return None

        if track.local_path and os.path.exists(track.local_path):
            self._logger.log_skip_existing(track_id, track.local_path)
            return track.local_path

        return None

    async def stream_or_download(self, track_id: int) -> Optional[str]:
        existing = await self.get_track_path(track_id)
        if existing:
            return existing

        track = await self._track_repo.get_by_id(track_id)
        if track is None:
            self._logger.log_track_not_found(track_id)
            return None

        artist_name = await self._get_artist_name(track)

        os.makedirs(self._download_dir, exist_ok=True)

        ext = ".mp3"
        dest_path = os.path.join(self._download_dir, f"{track_id}{ext}")

        track_info = TrackInfo(
            title=track.title,
            artist=artist_name,
            duration=track.duration,
        )

        result = await self._downloader.download(track_info, dest_path)
        if result is None:
            self._logger.log_download_failure(dest_path, reason="downloader returned None")
            return None

        track.local_path = result
        track.status = "downloaded"
        await self._track_repo.save(track)

        return result

    async def _get_artist_name(self, track: Track) -> str:
        artist = await self._artist_repo.get_by_id(track.artist_id)
        return artist.name if artist else str(track.artist_id)
