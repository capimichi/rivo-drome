# Soulseek Downloader (slskd) Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Soulseek downloader inside Rivo-Drome's Chain of Responsibility using the `slskd` API, allowing high-quality P2P track downloads with configurable timeouts and sharing folders across container boundaries.

**Architecture:** A new config class `SlskdConfig` and API client `SlskdClient` handle asynchronous communication with a separate `slskd` daemon. A new `SoulseekDownloader` subclass of `BaseDownloader` handles searching, result filtering (prioritizing `.flac` then `.mp3` at 320kbps), queue polling with timeouts, downloading, path normalization, file copy/cleanup, and integration into the Dependency Injection container.

**Tech Stack:** Python 3.11+, FastAPI, HTTPX (async), Injector (DI), Pytest (testing), Docker & Docker Compose.

## Global Constraints
- PEP 8 formatting with 4-space indentation; line length ≤100 chars.
- Type hints throughout; Pydantic models/explicit dataclasses for payloads.
- Snake_case for module/file names, CapWords for classes, snake_case for functions/variables.
- Thin FastAPI routes; delegate to services; wire dependencies via injector container construct.
- Use `@inject` on constructors for class dependencies.
- Bind explicitly only classes with literal params in DefaultContainer.
- Never retrieve config values using `DefaultContainer.getInstance()`. Avoid Service Locator.
- Avoid module-level constants (outside classes). Always define constants in class scope.
- Use `pytest` for tests. Name tests with `test_` prefix.

---

## File Structure Map
- **Modified**:
  - `.env.example`: Config templates for Navidrome and slskd directories.
  - `docker-compose.yml`: Mount mappings for host music/download paths.
  - `rivo_drome/container/default_container.py`: Register and inject `SlskdConfig`, `SlskdClient`, and `SoulseekDownloader`.
- **Created**:
  - `rivo_drome/config/slskd_config.py`: Configuration dataclass.
  - `rivo_drome/client/slskd_client.py`: API wrapper for slskd.
  - `rivo_drome/service/downloader/soulseek_downloader.py`: Downloader implementation.
  - `tests/service/test_slskd_config.py`: Configuration class unit tests.
  - `tests/client/test_slskd_client.py`: Client API mock unit tests.
  - `tests/service/downloader/test_soulseek_downloader.py`: Downloader flow unit tests.
  - `tests/service/test_default_container_soulseek.py`: Container wiring unit tests.

---

### Task 1: Environment Configuration & Compose File Setup

**Files:**
- Modify: `.env.example`
- Modify: `docker-compose.yml`

**Interfaces:**
- Produces: Environment variables `NAVIDROME_MUSIC_HOST_DIR`, `NAVIDROME_MUSIC_DIR`, `SLSKD_DOWNLOADS_HOST_DIR`, `SLSKD_DOWNLOADS_DIR`, `SLSKD_API_URL`, `SLSKD_API_KEY`, `SLSKD_SEARCH_TIMEOUT`, `SLSKD_DOWNLOAD_TIMEOUT`.

- [x] **Step 1: Add new environment variables to .env.example**
  Add the following lines under `# STORAGE` and `# SpotiFLAC REST API` sections in `.env.example`:
  ```bash
  # --- NAVIDROME DIRECTORIES ---
  NAVIDROME_MUSIC_HOST_DIR=/Users/michele/PycharmProjects/navidrome/music
  NAVIDROME_MUSIC_DIR=/app/var/navidrome_music

  # --- SOULSEEK (slskd) CONFIGURATION ---
  SLSKD_API_URL=http://host.docker.internal:5030
  SLSKD_API_KEY=
  SLSKD_DOWNLOADS_HOST_DIR=/Users/michele/PycharmProjects/slskd/downloads
  SLSKD_DOWNLOADS_DIR=/app/var/slskd/downloads
  SLSKD_SEARCH_TIMEOUT=10
  SLSKD_DOWNLOAD_TIMEOUT=60
  ```

- [x] **Step 2: Add host-to-container volume mappings to Rivo-Drome's docker-compose.yml**
  Modify `docker-compose.yml` to bind the directories from the environment. Update `services.proxy.volumes`:
  ```yaml
      volumes:
        - .:/app
        - ${NAVIDROME_MUSIC_HOST_DIR}:${NAVIDROME_MUSIC_DIR}
        - ${SLSKD_DOWNLOADS_HOST_DIR}:${SLSKD_DOWNLOADS_DIR}
  ```

- [x] **Step 3: Verify the docker-compose configuration**
  Run: `docker compose config`
  Expected: Config is printed without validation errors. (Make sure dummy default variables are handled or local `.env` has these filled to avoid unbound variable warnings).

---

### Task 2: Config Class (`SlskdConfig`)

**Files:**
- Create: `rivo_drome/config/slskd_config.py`
- Create: `tests/service/test_slskd_config.py`

**Interfaces:**
- Produces: `SlskdConfig` dataclass.

- [x] **Step 1: Write the config unit tests**
  Create `tests/service/test_slskd_config.py` with:
  ```python
  from rivo_drome.config.slskd_config import SlskdConfig

  def test_slskd_config_defaults():
      config = SlskdConfig()
      assert config.api_url == "http://localhost:5030"
      assert config.api_key == ""
      assert config.downloads_dir == "var/slskd/downloads"
      assert config.search_timeout == 10
      assert config.download_timeout == 60

  def test_slskd_config_custom():
      config = SlskdConfig(
          api_url="http://slskd.local:5030",
          api_key="secret",
          downloads_dir="/path/to/downloads",
          search_timeout=5,
          download_timeout=30
      )
      assert config.api_url == "http://slskd.local:5030"
      assert config.api_key == "secret"
      assert config.downloads_dir == "/path/to/downloads"
      assert config.search_timeout == 5
      assert config.download_timeout == 30
  ```

- [x] **Step 2: Run tests to verify they fail**
  Run: `pytest tests/service/test_slskd_config.py -v`
  Expected: FAIL (ModuleNotFound: No module named 'rivo_drome.config.slskd_config')

- [x] **Step 3: Implement `SlskdConfig` class**
  Create `rivo_drome/config/slskd_config.py` with:
  ```python
  from dataclasses import dataclass

  @dataclass
  class SlskdConfig:
      api_url: str = "http://localhost:5030"
      api_key: str = ""
      downloads_dir: str = "var/slskd/downloads"
      search_timeout: int = 10
      download_timeout: int = 60
  ```

- [x] **Step 4: Run tests to verify they pass**
  Run: `pytest tests/service/test_slskd_config.py -v`
  Expected: PASS

---

### Task 3: API Client (`SlskdClient`)

**Files:**
- Create: `rivo_drome/client/slskd_client.py`
- Create: `tests/client/test_slskd_client.py`

**Interfaces:**
- Consumes: `SlskdConfig`
- Produces: `SlskdClient` with async helper methods for searches and downloads.

- [x] **Step 1: Write failing mock unit tests for `SlskdClient`**
  Create `tests/client/test_slskd_client.py` with:
  ```python
  import pytest
  import httpx
  from unittest.mock import MagicMock
  from rivo_drome.config.slskd_config import SlskdConfig
  from rivo_drome.client.slskd_client import SlskdClient

  @pytest.fixture
  def config():
      return SlskdConfig(api_url="http://localhost:5030", api_key="test_key")

  @pytest.fixture
  def client(config):
      return SlskdClient(config)

  @pytest.mark.asyncio
  async def test_search(client, monkeypatch):
      mock_response = MagicMock(spec=httpx.Response)
      mock_response.status_code = 200
      mock_response.json.return_value = {"id": "search-uuid-123"}
      mock_response.raise_for_status = MagicMock()

      async def mock_post(*args, **kwargs):
          return mock_response

      monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

      search_id = await client.search("Queen - Bohemian Rhapsody")
      assert search_id == "search-uuid-123"

  @pytest.mark.asyncio
  async def test_get_search_responses(client, monkeypatch):
      mock_response = MagicMock(spec=httpx.Response)
      mock_response.status_code = 200
      mock_response.json.return_value = [{"username": "peer1", "files": []}]
      mock_response.raise_for_status = MagicMock()

      async def mock_get(*args, **kwargs):
          return mock_response

      monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

      responses = await client.get_search_responses("search-uuid-123")
      assert len(responses) == 1
      assert responses[0]["username"] == "peer1"
  ```

- [x] **Step 2: Run tests to verify they fail**
  Run: `pytest tests/client/test_slskd_client import -v`
  Expected: FAIL (ModuleNotFound: No module named 'rivo_drome.client.slskd_client')

- [x] **Step 3: Implement `SlskdClient`**
  Create `rivo_drome/client/slskd_client.py` with:
  ```python
  import logging
  import httpx
  from typing import List, dict, Optional
  from injector import inject
  from rivo_drome.config.slskd_config import SlskdConfig

  logger = logging.getLogger(__name__)

  class SlskdClient:
      @inject
      def __init__(self, config: SlskdConfig):
          self._base_url = config.api_url.rstrip("/")
          self._api_key = config.api_key
          self._headers = {"X-API-Key": self._api_key}

      async def search(self, query: str) -> Optional[str]:
          url = f"{self._base_url}/api/v0/searches"
          payload = {"searchText": query}
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.post(url, json=payload, headers=self._headers)
                  response.raise_for_status()
                  data = response.json()
                  return data.get("id")
              except Exception as e:
                  logger.error("SlskdClient search request failed: %s", e)
                  return None

      async def get_search_responses(self, search_id: str) -> List[dict]:
          url = f"{self._base_url}/api/v0/searches/{search_id}/responses"
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.get(url, headers=self._headers)
                  response.raise_for_status()
                  return response.json()
              except Exception as e:
                  logger.error("SlskdClient get_search_responses failed: %s", e)
                  return []

      async def delete_search(self, search_id: str) -> None:
          url = f"{self._base_url}/api/v0/searches/{search_id}"
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.delete(url, headers=self._headers)
                  response.raise_for_status()
              except Exception as e:
                  logger.warning("SlskdClient delete_search failed: %s", e)

      async def enqueue_download(self, username: str, filename: str, size: int) -> Optional[dict]:
          url = f"{self._base_url}/api/v0/transfers/downloads/{username}"
          payload = {"filename": filename, "size": size}
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.post(url, json=payload, headers=self._headers)
                  response.raise_for_status()
                  return response.json()
              except Exception as e:
                  logger.error("SlskdClient enqueue_download failed for user %s: %s", username, e)
                  return None

      async def get_downloads(self) -> List[dict]:
          url = f"{self._base_url}/api/v0/transfers/downloads"
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.get(url, headers=self._headers)
                  response.raise_for_status()
                  return response.json()
              except Exception as e:
                  logger.error("SlskdClient get_downloads failed: %s", e)
                  return []

      async def delete_download(self, username: str, id: str) -> None:
          url = f"{self._base_url}/api/v0/transfers/downloads/{username}/{id}"
          async with httpx.AsyncClient(timeout=10.0) as client:
              try:
                  response = await client.delete(url, headers=self._headers)
                  response.raise_for_status()
              except Exception as e:
                  logger.warning("SlskdClient delete_download failed for user %s and transfer id %s: %s", username, id, e)
  ```

- [x] **Step 4: Run tests to verify they pass**
  Run: `pytest tests/client/test_slskd_client.py -v`
  Expected: PASS

---

### Task 4: Downloader Integration (`SoulseekDownloader`)

**Files:**
- Create: `rivo_drome/service/downloader/soulseek_downloader.py`
- Create: `tests/service/downloader/test_soulseek_downloader.py`

**Interfaces:**
- Consumes: `SlskdClient`, `SlskdConfig`
- Produces: `SoulseekDownloader` class extending `BaseDownloader`.

- [x] **Step 1: Write mock tests for the downloader flow**
  Create `tests/service/downloader/test_soulseek_downloader.py` with:
  ```python
  import pytest
  import os
  import shutil
  from unittest.mock import AsyncMock, MagicMock, patch
  from rivo_drome.config.slskd_config import SlskdConfig
  from rivo_drome.client.slskd_client import SlskdClient
  from rivo_drome.model.track_info import TrackInfo
  from rivo_drome.service.downloader.soulseek_downloader import SoulseekDownloader

  @pytest.mark.asyncio
  async def test_do_download_success(tmp_path):
      downloads_dir = tmp_path / "downloads"
      downloads_dir.mkdir()
      
      # Mock the actual file written on disk
      mock_slskd_file_relative = "artist/album/song.flac"
      full_mock_file = downloads_dir / mock_slskd_file_relative
      full_mock_file.parent.mkdir(parents=True, exist_ok=True)
      with open(full_mock_file, "w") as f:
          f.write("mock binary music data")
          
      config = SlskdConfig(downloads_dir=str(downloads_dir), search_timeout=2, download_timeout=2)
      client = MagicMock(spec=SlskdClient)
      client.search = AsyncMock(return_value="search_id_123")
      
      # Mock search responses (FLAC and MP3)
      mock_responses = [
          {
              "username": "user1",
              "files": [
                  {
                      "filename": "artist\\album\\song.flac",
                      "size": 100,
                      "bitRate": 1411,
                      "extension": "flac"
                  },
                  {
                      "filename": "artist\\album\\song.mp3",
                      "size": 50,
                      "bitRate": 320,
                      "extension": "mp3"
                  }
              ]
          }
      ]
      client.get_search_responses = AsyncMock(return_value=mock_responses)
      client.enqueue_download = AsyncMock(return_value={"id": "transfer_id_456"})
      
      # Mock active downloads list: first Queued, then Succeeded
      client.get_downloads = AsyncMock()
      client.get_downloads.side_effect = [
          [{"username": "user1", "filename": "artist\\album\\song.flac", "id": "transfer_id_456", "state": "Queued"}],
          [{"username": "user1", "filename": "artist\\album\\song.flac", "id": "transfer_id_456", "state": "Succeeded"}]
      ]
      client.delete_search = AsyncMock()
      client.delete_download = AsyncMock()

      downloader = SoulseekDownloader(client, config)
      track_info = TrackInfo(title="song", artist="artist", album="album")
      dest_path = str(tmp_path / "final_song.flac")

      with patch("asyncio.sleep", AsyncMock()):
          result = await downloader._do_download(track_info, dest_path)

      assert result == dest_path
      assert os.path.exists(dest_path)
      client.enqueue_download.assert_called_once_with("user1", "artist\\album\\song.flac", 100)
      client.delete_search.assert_called_once_with("search_id_123")
      client.delete_download.assert_called_once_with("user1", "transfer_id_456")
  ```

- [x] **Step 2: Run tests to verify they fail**
  Run: `pytest tests/service/downloader/test_soulseek_downloader.py -v`
  Expected: FAIL (ModuleNotFound: No module named 'rivo_drome.service.downloader.soulseek_downloader')

- [x] **Step 3: Implement `SoulseekDownloader`**
  Create `rivo_drome/service/downloader/soulseek_downloader.py` with:
  ```python
  import logging
  import os
  import asyncio
  import shutil
  from typing import Optional, List, dict
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

          local_source_path = os.path.join(self._config.downloads_dir, normalized_relative_path)
          logger.info("SoulseekDownloader: looking for file locally at %s", local_source_path)

          if not os.path.exists(local_source_path):
              logger.error("SoulseekDownloader: completed download file not found at %s", local_source_path)
              await self._client.delete_download(username, transfer_id)
              return None

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

      def _select_best_file(self, responses: List[dict]) -> Optional[dict]:
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
  ```

- [x] **Step 4: Run tests to verify they pass**
  Run: `pytest tests/service/downloader/test_soulseek_downloader.py -v`
  Expected: PASS

---

### Task 5: Dependency Injection & Catena Registration

**Files:**
- Modify: `rivo_drome/container/default_container.py`
- Create: `tests/service/test_default_container_soulseek.py`

**Interfaces:**
- Consumes: `SoulseekDownloader`
- Produces: Correct container setup, binding configurations for `SlskdConfig` and `SlskdClient`, registration of `soulseek` in `DOWNLOADER_CHAIN` initialization.

- [x] **Step 1: Write container wiring verification tests**
  Create `tests/service/test_default_container_soulseek.py` with:
  ```python
  import pytest
  from unittest.mock import patch
  from rivo_drome.container.default_container import DefaultContainer
  from rivo_drome.config.slskd_config import SlskdConfig
  from rivo_drome.client.slskd_client import SlskdClient
  from rivo_drome.service.downloader.soulseek_downloader import SoulseekDownloader

  def test_default_container_slskd_wiring():
      mock_env = {
          "SLSKD_API_URL": "http://test-slskd-url:5030",
          "SLSKD_API_KEY": "test-api-key",
          "SLSKD_DOWNLOADS_DIR": "var/test/downloads",
          "SLSKD_SEARCH_TIMEOUT": "15",
          "SLSKD_DOWNLOAD_TIMEOUT": "90",
          "DOWNLOADER_CHAIN": "soulseek"
      }
      
      with patch.dict("os.environ", mock_env):
          container = DefaultContainer()
          
          # Verify config registration
          config = container.get(SlskdConfig)
          assert config.api_url == "http://test-slskd-url:5030"
          assert config.api_key == "test-api-key"
          assert config.downloads_dir == "var/test/downloads"
          assert config.search_timeout == 15
          assert config.download_timeout == 90
          
          # Verify client and downloader resolution
          client = container.get(SlskdClient)
          assert client is not None
          
          downloader = container.get(SoulseekDownloader)
          assert downloader is not None
  ```

- [x] **Step 2: Run tests to verify they fail**
  Run: `pytest tests/service/test_default_container_soulseek.py -v`
  Expected: FAIL (AssertionError or Config resolution errors)

- [x] **Step 3: Modify `rivo_drome/container/default_container.py`**
  Modify file by replacing/adding variables, imports, and binder configuration.
  
  Add imports at the top:
  ```python
  from rivo_drome.config.slskd_config import SlskdConfig
  from rivo_drome.client.slskd_client import SlskdClient
  from rivo_drome.service.downloader.soulseek_downloader import SoulseekDownloader
  ```

  Inside `_init_environment_variables(self)`:
  ```python
          # --- SLSKD Variables ---
          self.slskd_api_url = os.environ.get('SLSKD_API_URL', 'http://localhost:5030')
          self.slskd_api_key = os.environ.get('SLSKD_API_KEY', '')
          self.slskd_downloads_dir = os.environ.get('SLSKD_DOWNLOADS_DIR', 'var/slskd/downloads')
          self.slskd_search_timeout = int(os.environ.get('SLSKD_SEARCH_TIMEOUT', '10'))
          self.slskd_download_timeout = int(os.environ.get('SLSKD_DOWNLOAD_TIMEOUT', '60'))
  ```

  Inside `_init_bindings(self)`:
  ```python
          slskd_config = SlskdConfig(
              api_url=self.slskd_api_url,
              api_key=self.slskd_api_key,
              downloads_dir=self.slskd_downloads_dir,
              search_timeout=self.slskd_search_timeout,
              download_timeout=self.slskd_download_timeout
          )
          self.injector.binder.bind(SlskdConfig, to=slskd_config)
  ```

  Inside `_resolve_downloader_chain(self)` (or where `DOWNLOADER_CHAIN` is parsed and mapped):
  Let's look at `_resolve_downloader_chain` or downloader instantiation structure in `default_container.py`. 
  Wait, let's view `rivo_drome/container/default_container.py` lines 200 to 270 to verify how downloders are resolved.
  ```python
          # We map the string list downloader_chain_str to downloader instances
  ```
  We will add:
  `"soulseek": SoulseekDownloader` to the mapping dictionary.

- [x] **Step 4: Run tests to verify they pass**
  Run: `pytest tests/service/test_default_container_soulseek.py -v`
  Expected: PASS

---

### Task 6: Create External slskd Folder & Compose File

**Files:**
- Create: `/Users/michele/PycharmProjects/slskd/docker-compose.yml`

**Interfaces:**
- Produces: Agnostic slskd Docker orchestration configuration mapping downloads locally.

- [x] **Step 1: Write the slskd docker-compose file**
  Create the folder if it does not exist, and write `/Users/michele/PycharmProjects/slskd/docker-compose.yml` with:
  ```yaml
  version: '3.8'

  services:
    slskd:
      image: slskd/slskd:latest
      container_name: slskd
      ports:
        - "5030:5030"
      environment:
        - SLSKD_HTTP_PORT=5030
      volumes:
        - ./config:/app/config
        - ./downloads:/downloads
      restart: unless-stopped
  ```

- [x] **Step 2: Verify slskd docker compose syntax**
  Run: `docker compose -f /Users/michele/PycharmProjects/slskd/docker-compose.yml config`
  Expected: Output printed successfully with no syntax validation errors.
