import logging
import os
import asyncio
import shutil
from typing import Optional, List, Dict
from injector import inject
from rivo_drome.config.slskd_config import SlskdConfig
from rivo_drome.client.slskd_client import SlskdClient
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader

logger = logging.getLogger(__name__)

class SoulseekDownloader(BaseDownloader):
    @inject
    def __init__(self, client: SlskdClient, config: SlskdConfig):
        super().__init__()
        self._client = client
        self._config = config

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        query = f"{track_info.artist} - {track_info.title}"
        logger.info("SoulseekDownloader: starting search query '%s'", query)
        
        search_id = await self._client.search(query)
        if not search_id:
            logger.warning("SoulseekDownloader: search failed to initialize.")
            return None

        best_file = None
        search_limit = self._config.search_timeout
        elapsed_search = 0
        
        # 1. Search Polling Loop
        while elapsed_search < search_limit:
            responses = await self._client.get_search_responses(search_id)
            if responses:
                best_file = self._select_best_file(responses)
                if best_file:
                    break
            await asyncio.sleep(2)
            elapsed_search += 2

        # Clean up search
        await self._client.delete_search(search_id)

        if not best_file:
            logger.warning("SoulseekDownloader: no suitable files found for '%s'", query)
            return None

        username = best_file["username"]
        remote_filename = best_file["filename"]
        file_size = best_file["size"]

        logger.info("SoulseekDownloader: enqueuing file download from user '%s': %s", username, remote_filename)
        enqueue_res = await self._client.enqueue_download(username, remote_filename, file_size)
        if not enqueue_res:
            logger.error("SoulseekDownloader: enqueue request failed.")
            return None

        transfer_id = enqueue_res.get("id")
        if not transfer_id:
            logger.error("SoulseekDownloader: enqueue response did not contain a transfer ID.")
            return None

        # 2. Download Polling Loop
        download_limit = self._config.download_timeout
        elapsed_download = 0
        download_success = False

        while elapsed_download < download_limit:
            downloads = await self._client.get_downloads()
            matched_transfer = None
            for transfer in downloads:
                if transfer.get("username") == username and transfer.get("filename") == remote_filename:
                    matched_transfer = transfer
                    break

            if matched_transfer:
                state = matched_transfer.get("state")
                logger.info("SoulseekDownloader: current download state: %s", state)
                if state == "Succeeded":
                    download_success = True
                    break
                elif state in ["Errored", "Cancelled", "TimedOut", "Aborted", "Failed"]:
                    logger.warning("SoulseekDownloader: download transfer failed with state: %s", state)
                    break
            else:
                logger.warning("SoulseekDownloader: transfer not found in active downloads.")
                break

            await asyncio.sleep(3)
            elapsed_download += 3

        if not download_success:
            logger.warning("SoulseekDownloader: download failed or timed out. Cancelling/Deleting transfer record.")
            await self._client.delete_download(username, transfer_id)
            return None

        # 3. Handle Completed File copy/move
        # Normalise Windows path backslashes to forward slashes
        normalized_relative_path = remote_filename.replace("\\", "/")
        if normalized_relative_path.startswith("/"):
            normalized_relative_path = normalized_relative_path.lstrip("/")

        # Look in multiple possible locations where slskd might download the file
        possible_paths = [
            os.path.join(self._config.downloads_dir, normalized_relative_path),
            os.path.join(self._config.downloads_dir, username, normalized_relative_path),
            os.path.join(self._config.downloads_dir, "completed", username, normalized_relative_path),
            os.path.join(self._config.downloads_dir, "completed", normalized_relative_path),
        ]
        
        local_source_path = None
        for path in possible_paths:
            if os.path.exists(path):
                local_source_path = path
                break

        if not local_source_path:
            logger.error(
                "SoulseekDownloader: completed download file not found. Tried paths: %s", 
                possible_paths
            )
            await self._client.delete_download(username, transfer_id)
            return None

        logger.info("SoulseekDownloader: found file locally at %s", local_source_path)

        # Relocate to final destination path with correct extension
        output_dir = os.path.dirname(dest_path)
        os.makedirs(output_dir, exist_ok=True)
        _, ext = os.path.splitext(local_source_path)
        final_dest_path = os.path.splitext(dest_path)[0] + ext.lower()

        try:
            shutil.move(local_source_path, final_dest_path)
            logger.info("SoulseekDownloader: relocated downloaded file to: %s", final_dest_path)
        except Exception as e:
            logger.error("SoulseekDownloader: error relocating file: %s", e)
            await self._client.delete_download(username, transfer_id)
            return None

        # Clean up transfer logs
        await self._client.delete_download(username, transfer_id)
        return final_dest_path

    def _select_best_file(self, responses: List[Dict]) -> Optional[Dict]:
        best_candidate = None
        
        for response in responses:
            username = response.get("username")
            files = response.get("files", [])
            for f in files:
                filename = f.get("filename", "")
                extension = f.get("extension", "").lower().strip()
                bitrate = f.get("bitRate", 0)
                size = f.get("size", 0)
                
                if extension not in ["flac", "mp3"]:
                    continue

                candidate = {
                    "username": username,
                    "filename": filename,
                    "extension": extension,
                    "bitRate": bitrate,
                    "size": size
                }

                if best_candidate is None:
                    best_candidate = candidate
                    continue

                # Prefer FLAC over MP3
                if candidate["extension"] == "flac" and best_candidate["extension"] != "flac":
                    best_candidate = candidate
                elif candidate["extension"] != "flac" and best_candidate["extension"] == "flac":
                    continue
                else:
                    # If both are same extension, select higher bitrate
                    if candidate["bitRate"] > best_candidate["bitRate"]:
                        best_candidate = candidate
                    elif candidate["bitRate"] == best_candidate["bitRate"]:
                        # If same bitrate, select larger file (presumably better sample size)
                        if candidate["size"] > best_candidate["size"]:
                            best_candidate = candidate

        return best_candidate
