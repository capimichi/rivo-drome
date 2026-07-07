import asyncio
import os
from typing import Optional

import httpx
from injector import inject

from rivo_drome.client.jackett_client import JackettClient
from rivo_drome.client.torrserver_client import TorrServerClient
from rivo_drome.logger.torrent_downloader_logger import TorrentDownloaderLogger
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader


class TorrentDownloader(BaseDownloader):
    AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma"}

    @inject
    def __init__(
        self,
        jackett_client: JackettClient,
        torrserver_client: TorrServerClient,
        torrent_downloader_logger: TorrentDownloaderLogger,
    ):
        super().__init__()
        self._jackett = jackett_client
        self._torrserver = torrserver_client
        self._logger = torrent_downloader_logger

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        # Se abbiamo le info sull'album, proviamo a cercare l'album in torrent (molto più probabile trovare un torrent del intero album/discografia)
        queries = []
        if track_info.album:
            queries.append(f"{track_info.artist} {track_info.album}")
        queries.append(f"{track_info.artist} - {track_info.title}")

        results = []
        chosen_query = None
        for q in queries:
            results = await self._jackett.search(q)
            self._logger.log_search(q, len(results))
            if results:
                chosen_query = q
                break

        if not results:
            return None

        for result in results[:5]:
            magnet = result.get("Link") or result.get("Magnet")
            if not magnet:
                continue

            torrent_data = await self._torrserver.add_torrent(magnet)

            if torrent_data is None:
                continue

            info_hash = torrent_data.get("hash")
            if not info_hash:
                continue

            # TorrServer needs time to fetch metadata (especially for magnet links)
            torrent_info = None
            for _ in range(10):
                await asyncio.sleep(2)
                torrent_info = await self._torrserver.get_torrent_info(info_hash)
                if torrent_info and torrent_info.get("files"):
                    break

            if not torrent_info or not torrent_info.get("files"):
                continue


            files = torrent_info.get("files", [])
            audio_file = self._find_audio_file(files, track_info)
            if audio_file is None:
                continue

            file_index = audio_file.get("id")
            if file_index is None:
                continue

            # Conserve the extension of the torrent found
            audio_path = audio_file.get("path", audio_file.get("name", ""))
            _, ext = os.path.splitext(audio_path)
            if ext:
                dest_path = os.path.splitext(dest_path)[0] + ext.lower()

            stream_url = self._torrserver.get_file_stream_url(info_hash, file_index)
            return await self._download_file(stream_url, dest_path)

        return None

    def _find_audio_file(self, files: list, track_info: TrackInfo) -> Optional[dict]:
        import re
        # Cerchiamo di normalizzare il titolo per la ricerca (es. rimuovendo punteggiatura, spazi multipli)
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', track_info.title).lower()
        title_words = clean_title.split()

        for f in files:
            path = f.get("path", f.get("name", ""))
            ext = os.path.splitext(path)[1].lower()
            if ext in self.AUDIO_EXTENSIONS:
                path_lower = path.lower()
                # Verifica se tutte le parole significative del titolo della traccia sono presenti nel nome file del torrent
                if all(word in path_lower for word in title_words):
                    self._logger.log_audio_file_found(path)
                    return f
        # Se non troviamo corrispondenze col titolo, facciamo un fallback sul primo file audio (per torrent singoli)
        for f in files:
            path = f.get("path", f.get("name", ""))
            ext = os.path.splitext(path)[1].lower()
            if ext in self.AUDIO_EXTENSIONS:
                self._logger.log_audio_file_found(path)
                return f
        return None


    async def _download_file(self, url: str, dest_path: str) -> Optional[str]:
        self._logger.log_download_start(url, dest_path)
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with open(dest_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                    self._logger.log_download_success(dest_path)
                    return dest_path
        except Exception as e:
            self._logger.log_download_failure(dest_path, reason=str(e))
            return None
