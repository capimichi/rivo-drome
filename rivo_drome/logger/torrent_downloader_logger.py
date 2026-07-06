from typing import Optional

from rivo_drome.logger.abstract_logger import AbstractLogger


class TorrentDownloaderLogger(AbstractLogger):

    def __init__(self, log_dir: str):
        super().__init__(log_dir)

    def get_logger_name(self) -> str:
        return "torrent_downloader"

    def log_search(self, query: str, result_count: int) -> None:
        self.logger.info("Search query='%s' results=%d", query, result_count)

    def log_torrent_add(self, magnet: str, success: bool, info_hash: Optional[str] = None) -> None:
        self.logger.info(
            "Add torrent success=%s hash=%s magnet=%.80s...",
            success, info_hash, magnet,
        )

    def log_torrent_info(self, info_hash: str, file_count: int, has_audio: bool) -> None:
        self.logger.info("Torrent info hash=%s files=%d has_audio=%s", info_hash, file_count, has_audio)

    def log_download_start(self, url: str, dest_path: str) -> None:
        self.logger.info("Download start dest=%s", dest_path)

    def log_download_success(self, dest_path: str) -> None:
        self.logger.info("Download success dest=%s", dest_path)

    def log_download_failure(self, dest_path: str, reason: str = "") -> None:
        self.logger.info("Download failure dest=%s reason=%s", dest_path, reason)

    def log_skip_existing(self, track_id: int, path: str) -> None:
        self.logger.info("Skip existing track_id=%d path=%s", track_id, path)

    def log_track_not_found(self, track_id: int) -> None:
        self.logger.info("Track not found track_id=%d", track_id)

    def log_stream_url(self, info_hash: str, file_index: int, url: str) -> None:
        self.logger.info("Stream URL hash=%s file_index=%d url=%s", info_hash, file_index, url)

    def log_audio_file_found(self, file_path: str) -> None:
        self.logger.info("Audio file found path=%s", file_path)
