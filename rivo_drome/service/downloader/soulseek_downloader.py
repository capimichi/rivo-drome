import logging
import os
import asyncio
import shutil
import re
from typing import Optional, List, Dict
from injector import inject
from rivo_drome.config.slskd_config import SlskdConfig
from rivo_drome.client.slskd_client import SlskdClient
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.base_downloader import BaseDownloader
from rivo_drome.logger.soulseek_downloader_logger import SoulseekDownloaderLogger


class SoulseekDownloader(BaseDownloader):
    @inject
    def __init__(self, client: SlskdClient, config: SlskdConfig, logger: Optional[SoulseekDownloaderLogger] = None):
        super().__init__()
        self._client = client
        self._config = config
        if logger is None:
            class DummyLogger:
                def __init__(self):
                    self.logger = logging.getLogger("SoulseekDownloader")
            self._logger = DummyLogger()
        else:
            self._logger = logger

    async def _do_download(self, track_info: TrackInfo, dest_path: str) -> Optional[str]:
        cleaned_title = track_info.title
        cleaned_title = re.sub(r'[\(\[][^\]\)]*?(?:feat|ft|with|featuring)[^\]\)]*?[\)\]]', '', cleaned_title, flags=re.IGNORECASE)
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        query = f"{track_info.artist} - {cleaned_title}"
        self._logger.logger.info("SoulseekDownloader: starting search query '%s'", query)
        
        search_id = await self._client.search(query)
        if not search_id:
            self._logger.logger.warning("SoulseekDownloader: search failed to initialize.")
            return None

        final_responses = []
        search_limit = self._config.search_timeout
        elapsed_search = 0
        
        # 1. Search Polling Loop
        while elapsed_search < search_limit:
            responses = await self._client.get_search_responses(search_id)
            if responses:
                final_responses = responses
            
            status = await self._client.get_search_status(search_id)
            if status and status.get("isComplete"):
                self._logger.logger.info("SoulseekDownloader: search completed on slskd.")
                break
                
            await asyncio.sleep(2)
            elapsed_search += 2

        # Clean up search
        await self._client.delete_search(search_id)

        candidates = self._get_sorted_candidates(final_responses)
        if not candidates:
            self._logger.logger.warning("SoulseekDownloader: no suitable files found for '%s'", query)
            return None

        # Try enqueuing candidates in order of preference
        transfer_id = None
        chosen_candidate = None

        for candidate in candidates:
            username = candidate["username"]
            remote_filename = candidate["filename"]
            file_size = candidate["size"]

            self._logger.logger.info("SoulseekDownloader: enqueuing file download from user '%s': %s", username, remote_filename)
            enqueue_res = await self._client.enqueue_download(username, remote_filename, file_size)
            if not enqueue_res:
                self._logger.logger.warning("SoulseekDownloader: enqueue request failed for user '%s'. Trying next candidate...", username)
                continue

            enqueued_list = enqueue_res.get("enqueued", [])
            if enqueued_list and isinstance(enqueued_list, list):
                transfer_id = enqueued_list[0].get("id")

            if transfer_id:
                chosen_candidate = candidate
                break
            else:
                self._logger.logger.warning("SoulseekDownloader: enqueue response for user '%s' did not contain a transfer ID. Trying next...", username)

        if not chosen_candidate or not transfer_id:
            self._logger.logger.error("SoulseekDownloader: failed to enqueue download from any candidate.")
            return None

        username = chosen_candidate["username"]
        remote_filename = chosen_candidate["filename"]

        # 2. Download Polling Loop
        download_limit = self._config.download_timeout
        elapsed_download = 0
        download_success = False

        while elapsed_download < download_limit:
            downloads = await self._client.get_downloads()
            flat_downloads = []
            for item in downloads:
                if "directories" in item:
                    for dir_item in item.get("directories", []):
                        for file_item in dir_item.get("files", []):
                            flat_downloads.append(file_item)
                else:
                    flat_downloads.append(item)
                    
            matched_transfer = None
            for transfer in flat_downloads:
                if transfer.get("username") == username and transfer.get("filename") == remote_filename:
                    matched_transfer = transfer
                    break

            if matched_transfer:
                state = matched_transfer.get("state")
                self._logger.logger.info("SoulseekDownloader: current download state: %s", state)
                if "Succeeded" in state:
                    download_success = True
                    break
                elif any(s in state for s in ["Errored", "Cancelled", "TimedOut", "Aborted", "Failed"]):
                    self._logger.logger.warning("SoulseekDownloader: download transfer failed with state: %s", state)
                    break
            else:
                self._logger.logger.warning("SoulseekDownloader: transfer not found in active downloads.")
                break

            await asyncio.sleep(3)
            elapsed_download += 3

        if not download_success:
            self._logger.logger.warning("SoulseekDownloader: download failed or timed out. Cancelling/Deleting transfer record.")
            await self._client.delete_download(username, transfer_id)
            return None

        # 3. Handle Completed File copy/move
        target_filename = os.path.basename(remote_filename.replace("\\", "/"))
        local_source_path = None
        
        # Search recursively under downloads_dir for the target filename
        for root, dirs, files in os.walk(self._config.downloads_dir):
            if target_filename in files:
                local_source_path = os.path.join(root, target_filename)
                break

        if not local_source_path:
            self._logger.logger.error(
                "SoulseekDownloader: completed download file not found under %s for filename: %s", 
                self._config.downloads_dir,
                target_filename
            )
            await self._client.delete_download(username, transfer_id)
            return None

        self._logger.logger.info("SoulseekDownloader: found file locally at %s", local_source_path)

        # Relocate to final destination path with correct extension
        output_dir = os.path.dirname(dest_path)
        os.makedirs(output_dir, exist_ok=True)
        _, ext = os.path.splitext(local_source_path)
        final_dest_path = os.path.splitext(dest_path)[0] + ext.lower()

        try:
            shutil.move(local_source_path, final_dest_path)
            self._logger.logger.info("SoulseekDownloader: relocated downloaded file to: %s", final_dest_path)
        except Exception as e:
            self._logger.logger.error("SoulseekDownloader: error relocating file: %s", e)
            await self._client.delete_download(username, transfer_id)
            return None

        # Clean up transfer logs
        await self._client.delete_download(username, transfer_id)
        return final_dest_path

    def _get_sorted_candidates(self, responses: List[Dict]) -> List[Dict]:
        candidates = []
        for response in responses:
            username = response.get("username")
            files = response.get("files", [])
            for f in files:
                filename = f.get("filename", "")
                extension = f.get("extension", "").lower().strip()
                if not extension:
                    _, ext_from_filename = os.path.splitext(filename)
                    extension = ext_from_filename.lower().lstrip(".")
                
                bitrate = f.get("bitRate", 0)
                size = f.get("size", 0)
                
                if extension not in ["flac", "mp3", "m4a"]:
                    continue

                candidates.append({
                    "username": username,
                    "filename": filename,
                    "extension": extension,
                    "bitRate": bitrate,
                    "size": size
                })
        
        # Sort candidates
        def sort_key(c):
            ext_map = {"flac": 3, "mp3": 2, "m4a": 1}
            return (ext_map.get(c["extension"], 0), c["bitRate"], c["size"])
            
        candidates.sort(key=sort_key, reverse=True)
        return candidates

    def _select_best_file(self, responses: List[Dict]) -> Optional[Dict]:
        candidates = self._get_sorted_candidates(responses)
        return candidates[0] if candidates else None
