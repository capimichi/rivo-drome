# SpotiFLAC Downloader Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement a new SpotiFLAC downloader that resolves track URLs via the Odesli (Songlink) API and downloads the audio using a local `spotiflac-rest-api` instance.

**Architecture:** A new configuration class `SpotiFlacConfig` holds API settings. An `OdesliClient` resolves a track's Deezer URL to Qobuz, Amazon Music, and Tidal URLs. A `SpotiFlacClient` calls the `/api/download/sync` endpoint of SpotiFLAC REST API. Finally, `SpotiFlacDownloader` inherits from `BaseDownloader` and tries each resolved URL sequentially.

**Tech Stack:** Python 3, FastAPI, httpx, pytest, injector, pytest-mock.

## Global Constraints

- Keep FastAPI routes thin: delegate to services; wire dependencies via the injector container.
- Always use Dependency Injection via `@inject` from `injector` for class dependencies. Place `@inject` on constructors so that services, controllers, etc., automatically resolve their dependencies without explicit configuration.
- In `DefaultContainer`, within the `_init_bindings` method, explicitly bind to `injector` only the classes that require a literal variable during initialization (e.g., environment configurations). If a class only requires other classes in its constructor, it will receive them implicitly from `injector`; do not explicitly bind them in `_init_bindings` to avoid redundant code.
- Never resolve dependencies or retrieve configuration values inside classes using `DefaultContainer.getInstance()`. Avoid the Service Locator pattern.
- Avoid defining constants at the module level (outside classes). Always define constants within the class scope where they are used to keep namespaces clean and improve modularity.

---

### Task 1: SpotiFlacConfig

**Files:**
- Create: `rivo_drome/config/spotiflac_config.py`
- Test: `tests/service/test_spotiflac_config.py`

**Interfaces:**
- Consumes: None
- Produces: `SpotiFlacConfig` dataclass with attributes `base_url` (str), `username` (Optional[str]), and `password` (Optional[str]).

- [x] **Step 1: Write the failing test**

Create `tests/service/test_spotiflac_config.py`:
```python
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

def test_spotiflac_config_defaults():
    config = SpotiFlacConfig()
    assert config.base_url == "http://localhost:8080"
    assert config.username is None
    assert config.password is None

def test_spotiflac_config_custom():
    config = SpotiFlacConfig(base_url="http://my-spotiflac:9000", username="admin", password="password123")
    assert config.base_url == "http://my-spotiflac:9000"
    assert config.username == "admin"
    assert config.password == "password123"
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_spotiflac_config.py`
Expected: FAIL due to missing `rivo_drome.config.spotiflac_config`.

- [x] **Step 3: Write minimal implementation**

Create `rivo_drome/config/spotiflac_config.py`:
```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpotiFlacConfig:
    base_url: str = "http://localhost:8080"
    username: Optional[str] = None
    password: Optional[str] = None
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_spotiflac_config.py`
Expected: PASS

---

### Task 2: TrackInfo Modification

**Files:**
- Modify: `rivo_drome/model/track_info.py`
- Modify: `rivo_drome/service/stream_service.py`

**Interfaces:**
- Consumes: `Track` model from DB (specifically `track.deezer_id`).
- Produces: `TrackInfo` with an additional `deezer_id: Optional[int] = None` attribute.

- [x] **Step 1: Write the failing test**

Modify `tests/service/test_stream_service.py` or write a minimal unit test to check `TrackInfo` instantiation with `deezer_id` by modifying the imports. Let's create `tests/service/test_track_info.py`:
```python
from rivo_drome.model.track_info import TrackInfo

def test_track_info_has_deezer_id():
    ti = TrackInfo(title="Test", artist="Artist", deezer_id=12345)
    assert ti.deezer_id == 12345
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_track_info.py`
Expected: FAIL due to `TypeError: __init__() got an unexpected keyword argument 'deezer_id'`.

- [x] **Step 3: Write minimal implementation**

Modify `rivo_drome/model/track_info.py`:
```python
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TrackInfo:
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None
    track_number: Optional[int] = None
    alternative_albums: List[str] = field(default_factory=list)
    deezer_id: Optional[int] = None
```

Modify `rivo_drome/service/stream_service.py` at the `TrackInfo` instantiation in `stream_or_download` (lines 125-132):
```python
        # 2. Generazione del Path per il Download
        track_info = TrackInfo(
            title=track.title,
            artist=artist_name,
            album=album_name,
            duration=track.duration,
            track_number=track.track_number,
            alternative_albums=alternative_albums,
            deezer_id=track.deezer_id,
        )
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_track_info.py`
Expected: PASS

---

### Task 3: OdesliClient

**Files:**
- Create: `rivo_drome/client/odesli_client.py`
- Test: `tests/service/test_odesli_client.py`

**Interfaces:**
- Consumes: `deezer_id` (int).
- Produces: `OdesliClient.get_track_links(deezer_id: int) -> Dict[str, Optional[str]]` returning resolved Qobuz, Tidal, and Amazon Music URLs.

- [x] **Step 1: Write the failing test**

Create `tests/service/test_odesli_client.py`:
```python
import pytest
import respx
from httpx import Response
from rivo_drome.client.odesli_client import OdesliClient

@pytest.mark.asyncio
@respx.mock
async def test_odesli_client_success():
    deezer_id = 12345
    target_url = f"https://api.odesli.co/v1/links?url=https://www.deezer.com/track/{deezer_id}&userCountry=IT"
    
    mock_response = {
        "linksByPlatform": {
            "qobuz": {"url": "https://open.qobuz.com/track/qobuz_123"},
            "tidal": {"url": "https://tidal.com/track/tidal_123"},
            "amazonMusic": {"url": "https://music.amazon.com/tracks/amazon_123"}
        }
    }
    respx.get(target_url).mock(return_value=Response(200, json=mock_response))
    
    client = OdesliClient()
    links = await client.get_track_links(deezer_id)
    assert links["qobuz"] == "https://open.qobuz.com/track/qobuz_123"
    assert links["tidal"] == "https://tidal.com/track/tidal_123"
    assert links["amazonMusic"] == "https://music.amazon.com/tracks/amazon_123"

@pytest.mark.asyncio
@respx.mock
async def test_odesli_client_failure():
    deezer_id = 12345
    target_url = f"https://api.odesli.co/v1/links?url=https://www.deezer.com/track/{deezer_id}&userCountry=IT"
    respx.get(target_url).mock(return_value=Response(500))
    
    client = OdesliClient()
    links = await client.get_track_links(deezer_id)
    assert links == {}
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_odesli_client.py`
Expected: FAIL due to missing `OdesliClient` import.

- [x] **Step 3: Write minimal implementation**

Create `rivo_drome/client/odesli_client.py`:
```python
import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OdesliClient:
    API_URL = "https://api.odesli.co/v1/links"

    async def get_track_links(self, deezer_id: int) -> Dict[str, Optional[str]]:
        deezer_url = f"https://www.deezer.com/track/{deezer_id}"
        params = {
            "url": deezer_url,
            "userCountry": "IT"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                links = {}
                links_by_platform = data.get("linksByPlatform", {})
                for platform in ["qobuz", "tidal", "amazonMusic"]:
                    if platform in links_by_platform:
                        links[platform] = links_by_platform[platform].get("url")
                return links
            except Exception as e:
                logger.error("Odesli link resolution failed for deezer_id %s: %s", deezer_id, e)
                return {}
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_odesli_client.py`
Expected: PASS

---

### Task 4: SpotiFlacClient

**Files:**
- Create: `rivo_drome/client/spotiflac_client.py`
- Test: `tests/service/test_spotiflac_client.py`

**Interfaces:**
- Consumes: `SpotiFlacConfig` configuration object.
- Produces: `SpotiFlacClient.download_sync(url: str, service: str, quality: str, output_dir: str) -> Optional[str]` which calls `POST /api/download/sync` and returns the file path of the downloaded file.

- [x] **Step 1: Write the failing test**

Create `tests/service/test_spotiflac_client.py`:
```python
import pytest
import respx
from httpx import Response
from rivo_drome.client.spotiflac_client import SpotiFlacClient
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

@pytest.mark.asyncio
@respx.mock
async def test_spotiflac_client_download_success():
    config = SpotiFlacConfig(base_url="http://test-server")
    client = SpotiFlacClient(config)
    
    mock_payload = {
        "url": "https://open.qobuz.com/track/123",
        "service": "qobuz",
        "quality": "6",
        "output_dir": "/tmp/downloads"
    }
    
    mock_response = {
        "status": "completed",
        "files": ["/tmp/downloads/Queen - Bohemian Rhapsody.flac"]
    }
    
    respx.post("http://test-server/api/download/sync", json=mock_payload).mock(
        return_value=Response(200, json=mock_response)
    )
    
    file_path = await client.download_sync(
        url="https://open.qobuz.com/track/123",
        service="qobuz",
        quality="6",
        output_dir="/tmp/downloads"
    )
    
    assert file_path == "/tmp/downloads/Queen - Bohemian Rhapsody.flac"

@pytest.mark.asyncio
@respx.mock
async def test_spotiflac_client_download_failure():
    config = SpotiFlacConfig(base_url="http://test-server")
    client = SpotiFlacClient(config)
    
    respx.post("http://test-server/api/download/sync").mock(
        return_value=Response(500)
    )
    
    file_path = await client.download_sync(
        url="https://open.qobuz.com/track/123",
        service="qobuz",
        quality="6",
        output_dir="/tmp/downloads"
    )
    
    assert file_path is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_spotiflac_client.py`
Expected: FAIL due to missing `SpotiFlacClient` import.

- [x] **Step 3: Write minimal implementation**

Create `rivo_drome/client/spotiflac_client.py`:
```python
import logging
import httpx
from typing import Optional
from injector import inject
from rivo_drome.config.spotiflac_config import SpotiFlacConfig

logger = logging.getLogger(__name__)


class SpotiFlacClient:
    @inject
    def __init__(self, config: SpotiFlacConfig):
        self._base_url = config.base_url.rstrip("/")
        self._username = config.username
        self._password = config.password

    async def download_sync(self, url: str, service: str, quality: str, output_dir: str) -> Optional[str]:
        target_url = f"{self._base_url}/api/download/sync"
        payload = {
            "url": url,
            "service": service,
            "quality": quality,
            "output_dir": output_dir
        }
        
        auth = None
        if self._username and self._password:
            auth = (self._username, self._password)

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(target_url, json=payload, auth=auth)
                response.raise_for_status()
                data = response.json()
                
                files = data.get("files", [])
                if files and data.get("status") == "completed":
                    return files[0]
                return None
            except Exception as e:
                logger.error("SpotiFLAC REST API download request failed for url %s: %s", url, e)
                return None
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_spotiflac_client.py`
Expected: PASS

---

### Task 5: SpotiFlacDownloader

**Files:**
- Create: `rivo_drome/service/downloader/spotiflac_downloader.py`
- Test: `tests/service/downloader/test_spotiflac_downloader.py`

**Interfaces:**
- Consumes: `OdesliClient`, `SpotiFlacClient`, `TrackInfo`.
- Produces: `SpotiFlacDownloader._do_download(track_info: TrackInfo, dest_path: str) -> Optional[str]`.

- [x] **Step 1: Write the failing test**

Create `tests/service/downloader/test_spotiflac_downloader.py`:
```python
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.service.downloader.spotiflac_downloader import SpotiFlacDownloader
from rivo_drome.client.odesli_client import OdesliClient
from rivo_drome.client.spotiflac_client import SpotiFlacClient

@pytest.mark.asyncio
async def test_spotiflac_downloader_success(tmp_path):
    odesli_client = MagicMock(spec=OdesliClient)
    spotiflac_client = MagicMock(spec=SpotiFlacClient)
    
    track_info = TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        deezer_id=12345
    )
    
    mock_links = {
        "qobuz": "https://open.qobuz.com/track/qobuz_123",
        "amazonMusic": "https://music.amazon.com/tracks/amazon_123",
        "tidal": "https://tidal.com/track/tidal_123"
    }
    odesli_client.get_track_links = AsyncMock(return_value=mock_links)
    
    # Mocking that Qobuz fails but Amazon succeeds
    spotiflac_client.download_sync = AsyncMock()
    
    # We must mock file creation on success
    temp_downloaded_file = tmp_path / "downloads" / "Queen - Bohemian Rhapsody.flac"
    
    def side_effect(url, service, quality, output_dir):
        if service == "qobuz":
            return None
        elif service == "amazon":
            os.makedirs(os.path.dirname(temp_downloaded_file), exist_ok=True)
            with open(temp_downloaded_file, "w") as f:
                f.write("audio content")
            return str(temp_downloaded_file)
        return None
        
    spotiflac_client.download_sync.side_effect = side_effect
    
    downloader = SpotiFlacDownloader(odesli_client, spotiflac_client)
    
    dest_path = str(tmp_path / "music" / "Queen" / "Bohemian Rhapsody.mp3")
    
    result = await downloader._do_download(track_info, dest_path)
    
    assert result == dest_path
    assert os.path.exists(dest_path)
    
    # Ensure Qobuz was tried first, then Amazon (which succeeded), and Tidal was not tried
    assert spotiflac_client.download_sync.call_count == 2
    spotiflac_client.download_sync.assert_any_call("https://open.qobuz.com/track/qobuz_123", "qobuz", "6", os.path.dirname(dest_path))
    spotiflac_client.download_sync.assert_any_call("https://music.amazon.com/tracks/amazon_123", "amazon", "", os.path.dirname(dest_path))
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/downloader/test_spotiflac_downloader.py`
Expected: FAIL due to missing `SpotiFlacDownloader` class.

- [x] **Step 3: Write minimal implementation**

Create `rivo_drome/service/downloader/spotiflac_downloader.py`:
```python
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
                output_dir=output_dir
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
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/downloader/test_spotiflac_downloader.py`
Expected: PASS

---

### Task 6: Wiring inside DefaultContainer & Configuration

**Files:**
- Modify: `rivo_drome/container/default_container.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: `SPOTIFLAC_API_URL`, `SPOTIFLAC_USERNAME`, `SPOTIFLAC_PASSWORD`, and `DOWNLOADER_CHAIN` from `.env`.
- Produces: Wire `SpotiFlacConfig` to binder. Initialize and link `SpotiFlacDownloader` inside the downloader chain.

- [x] **Step 1: Write the failing test**

Let's modify `tests/service/test_stream_service.py` to assert that `spotiflac` is a valid entry in the chain, or verify `DefaultContainer` initialization behavior. Let's add a test to `tests/service/test_stream_service.py` or a dedicated test `tests/service/test_default_container_spotiflac.py`:
```python
import os
from unittest.mock import patch
from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.config.spotiflac_config import SpotiFlacConfig
from rivo_drome.service.downloader.spotiflac_downloader import SpotiFlacDownloader

def test_default_container_wires_spotiflac():
    env = {
        "DOWNLOADER_CHAIN": "spotiflac,youtube",
        "SPOTIFLAC_API_URL": "http://my-custom-spotiflac:1234",
        "SPOTIFLAC_USERNAME": "admin",
        "SPOTIFLAC_PASSWORD": "pwd"
    }
    with patch.dict(os.environ, env):
        # Reset container instance for testing
        DefaultContainer.instance = None
        container = DefaultContainer.getInstance()
        
        config = container.get(SpotiFlacConfig)
        assert config.base_url == "http://my-custom-spotiflac:1234"
        assert config.username == "admin"
        assert config.password == "pwd"
        
        first_downloader = container.get(SpotiFlacDownloader)
        assert first_downloader is not None
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_default_container_spotiflac.py`
Expected: FAIL due to missing config binding and lack of support for `"spotiflac"` chain resolution.

- [x] **Step 3: Write minimal implementation**

First, modify `rivo_drome/container/default_container.py` to:
1. Import `SpotiFlacConfig` and `SpotiFlacDownloader` at the top:
```python
from rivo_drome.config.spotiflac_config import SpotiFlacConfig
from rivo_drome.service.downloader.spotiflac_downloader import SpotiFlacDownloader
```
2. Read SpotiFLAC env vars in `_init_environment_variables()`:
```python
        self.spotiflac_api_url = os.environ.get('SPOTIFLAC_API_URL', 'http://localhost:8080')
        self.spotiflac_username = os.environ.get('SPOTIFLAC_USERNAME', None)
        self.spotiflac_password = os.environ.get('SPOTIFLAC_PASSWORD', None)
```
3. Bind `SpotiFlacConfig` in `_init_bindings()`:
```python
        spotiflac_config = SpotiFlacConfig(
            base_url=self.spotiflac_api_url,
            username=self.spotiflac_username,
            password=self.spotiflac_password,
        )
        self.injector.binder.bind(SpotiFlacConfig, to=spotiflac_config)
```
4. Update the downloader chain constructor in `_init_bindings()` around line 204:
```python
        chain_order = [s.strip() for s in self.downloader_chain_str.split(",") if s.strip()]
        downloaders = {}
        if "torrent" in chain_order:
            downloaders["torrent"] = TorrentDownloader(
                jackett_client, torrserver_client, torrent_downloader_logger
            )

        if "youtube" in chain_order:
            downloaders["youtube"] = YoutubeDownloader()

        if "spotiflac" in chain_order:
            # Resolute clients implicitly from the injector
            odesli_client = self.injector.get(OdesliClient) # Wait, need import at top
            spotiflac_client = self.injector.get(SpotiFlacClient) # Wait, need import at top
            downloaders["spotiflac"] = SpotiFlacDownloader(odesli_client, spotiflac_client)
```
Wait! Make sure `OdesliClient` and `SpotiFlacClient` are imported at the top of `rivo_drome/container/default_container.py`:
```python
from rivo_drome.client.odesli_client import OdesliClient
from rivo_drome.client.spotiflac_client import SpotiFlacClient
```

Let's modify `DefaultContainer._init_bindings` chain generation carefully:
```python
        if "spotiflac" in chain_order:
            # Let the injector resolve OdesliClient and SpotiFlacClient automatically
            # We import OdesliClient and SpotiFlacClient in DefaultContainer
            odesli_client = self.injector.get(OdesliClient)
            spotiflac_client = self.injector.get(SpotiFlacClient)
            downloaders["spotiflac"] = SpotiFlacDownloader(
                odesli_client=odesli_client,
                spotiflac_client=spotiflac_client
            )
```

Also, modify `.env.example` to add:
```bash
# SpotiFLAC REST API
SPOTIFLAC_API_URL=http://localhost:8080
SPOTIFLAC_USERNAME=
SPOTIFLAC_PASSWORD=
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_default_container_spotiflac.py`
Expected: PASS

---

## Plan Self-Review Check

1. **Spec coverage**:
   - SpotiFlacConfig created and loads from `.env`: Handled in Task 1 & Task 6.
   - OdesliClient resolves Deezer URL to Qobuz, Tidal, Amazon: Handled in Task 3.
   - SpotiFlacClient calls `/api/download/sync`: Handled in Task 4.
   - SpotiFlacDownloader tries sequentially in chain: Handled in Task 5.
   - Env variables registered in DefaultContainer: Handled in Task 6.
2. **Placeholder scan**: Checked; no TBD, TODO, or vague statements. Complete implementation snippets are written out.
3. **Type consistency**: Checked; OdesliClient returns `Dict[str, Optional[str]]`, SpotiFlacClient returns `Optional[str]`, SpotiFlacDownloader uses these types consistently.

