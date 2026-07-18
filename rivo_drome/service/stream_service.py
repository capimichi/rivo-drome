import os
import uuid
from typing import Optional
from fastapi import HTTPException
from rivo_drome.manager.queue_manager import QueueManager
from rivo_drome.model.queue_task import DownloadTaskPayload

from injector import inject

from rivo_drome.entity.track import Track
from rivo_drome.entity.album import Album
from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.repository.album_repository import AlbumRepository
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.track_repository import TrackRepository
from rivo_drome.service.downloader.base_downloader import BaseDownloader
from rivo_drome.client.navidrome_client import NavidromeClient
from rivo_drome.client.deezer_client import DeezerClient
from rivo_drome.client.musicbrainz_client import MusicBrainzClient
from rivo_drome.config.navidrome_config import NavidromeConfig


class StreamService:
    @inject
    def __init__(
        self,
        track_repository: TrackRepository,
        artist_repository: ArtistRepository,
        album_repository: AlbumRepository,
        downloader_chain: BaseDownloader,
        download_dir: str,
        torrent_downloader_logger: TorrentDownloaderLogger,
        navidrome_client: NavidromeClient,
        navidrome_config: NavidromeConfig,
        deezer_client: DeezerClient,
        musicbrainz_client: MusicBrainzClient,
        queue_manager: QueueManager = None,
    ):
        self._track_repo = track_repository
        self._artist_repo = artist_repository
        self._album_repo = album_repository
        self._downloader = downloader_chain
        self._download_dir = download_dir
        self._logger = torrent_downloader_logger
        self._navidrome_client = navidrome_client
        self._navidrome_config = navidrome_config
        self._deezer_client = deezer_client
        self._musicbrainz_client = musicbrainz_client
        self._queue_manager = queue_manager

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

        # 1. Controllo Preventivo su Navidrome
        navidrome_path = await self._navidrome_client.search_track(artist_name, track.title)
        if navidrome_path:
            base_dir = self._navidrome_config.music_dir or self._download_dir
            absolute_path = os.path.join(base_dir, navidrome_path)
            if os.path.exists(absolute_path):
                track.local_path = absolute_path
                track.status = "downloaded"
                await self._track_repo.save(track)
                return absolute_path

        # Resolve alternative albums from MusicBrainz and Deezer
        alt_album_titles = await self._musicbrainz_client.get_alternative_albums(artist_name, track.title)
        alt_albums_found = []
        for alt_title in alt_album_titles:
            search_query = f"{artist_name} {alt_title}"
            deezer_result = await self._deezer_client.search_album(search_query, limit=5)
            albums_data = deezer_result.get("data", [])
            if not albums_data:
                continue
            
            best_match = None
            for item in albums_data:
                if item.get("title", "").lower().strip() == alt_title.lower().strip():
                    best_match = item
                    break
            if not best_match:
                best_match = albums_data[0]
                
            album_id = best_match.get("id")
            if album_id:
                existing_album = await self._album_repo.find_by_deezer_id(album_id)
                if not existing_album:
                    existing_album = Album(
                        title=best_match.get("title", "Unknown"),
                        artist_id=track.artist_id,
                        cover_url=best_match.get("cover_big") or best_match.get("cover_medium"),
                        deezer_id=album_id,
                    )
                    existing_album = await self._album_repo.save(existing_album)
                
                alt_albums_found.append(existing_album)

        modified = False
        for alb in alt_albums_found:
            if not any(a.id == alb.id for a in track.albums):
                track.albums.append(alb)
                modified = True
                
        if modified:
            await self._track_repo.save(track)

        album_name = track.albums[0].title if track.albums else None
        alternative_albums = [a.title for a in track.albums[1:]]

        # 2. Generazione del Path per il Download
        if self._queue_manager:
            task = DownloadTaskPayload(
                task_id=str(uuid.uuid4()),
                song_id=track.id,
                artist_name=artist_name,
                title=track.title
            )
            self._queue_manager.enqueue_task("download", task)
            raise HTTPException(status_code=404, detail="Audio in coda di download.")

        return await self.process_download(track.id)

    async def process_download(self, track_id: int) -> Optional[str]:
        track = await self._track_repo.get_by_id(track_id)
        if track is None:
            return None
            
        artist_name = await self._get_artist_name(track)
        album_name = track.albums[0].title if track.albums else None
        alternative_albums = [a.title for a in track.albums[1:]]

        track_info = TrackInfo(
            title=track.title,
            artist=artist_name,
            album=album_name,
            duration=track.duration,
            track_number=track.track_number,
            alternative_albums=alternative_albums,
            deezer_id=track.deezer_id,
        )

        from rivo_drome.helper.path_helper import build_structured_path
        dest_path = build_structured_path(self._download_dir, track_info, ".mp3")

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        result = await self._downloader.download(track_info, dest_path)
        if result is None:
            self._logger.log_download_failure(dest_path, reason="downloader returned None")
            return None

        track.local_path = result
        track.status = "downloaded"
        await self._track_repo.save(track)

        # 3. Rescan Post-Download
        await self._navidrome_client.trigger_rescan()

        return result

    async def _get_artist_name(self, track: Track) -> str:
        artist = await self._artist_repo.get_by_id(track.artist_id)
        return artist.name if artist else str(track.artist_id)
