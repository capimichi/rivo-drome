# Audio Queue Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an asynchronous task queue using Redis and a custom cron worker to handle audio downloads and conversions in the background.

**Architecture:** We will run a `redis` container and a new `cron` container. The API/Service will use a `QueueManager` with `redis-py` (using ZSETs and Lists via pipeline) to atomically enqueue tasks and prevent duplicate downloads. The cron worker will continuously poll the queue and execute the tasks asynchronously.

**Tech Stack:** Python, FastAPI, Redis, Pydantic, Click.

## Global Constraints

- Source lives under `rivo_drome/`, split by responsibility.
- Use explicit Pydantic models for payloads.
- Use Dependency Injection via `@inject` from `injector`.
- No constants at the module level.
- Write tests for new logic (pytest).

---

### Task 1: Update Infrastructure and Dependencies

**Files:**
- Modify: `docker-compose.yml`
- Modify: `requirements.txt`
- Modify: `.env.example`

**Interfaces:**
- Produces: Redis service available on port 6379, Cron service running `python -m rivo_drome.cli cron`.

- [ ] **Step 1: Add Redis to requirements**
Add `redis` to `requirements.txt`.

- [ ] **Step 2: Update docker-compose.yml**
Add a `redis` service (e.g. `redis:7-alpine`) with a `redis_data` volume. Add a `cron` service that uses the same build context as `proxy` but runs `python -m rivo_drome.cli cron`. Inject `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`.

- [ ] **Step 3: Update .env.example**
Add `REDIS_HOST=redis`, `REDIS_PORT=6379`, `REDIS_PASSWORD=`.

---

### Task 2: Create Queue Models

**Files:**
- Create: `rivo_drome/model/queue_task.py`

**Interfaces:**
- Produces: `BaseQueueTask`, `DownloadTaskPayload`, `ConversionTaskPayload` Pydantic models.

- [ ] **Step 1: Write the models**
```python
from pydantic import BaseModel
from typing import Optional

class BaseQueueTask(BaseModel):
    task_id: str

class DownloadTaskPayload(BaseQueueTask):
    song_id: int
    artist_name: str
    title: str

class ConversionTaskPayload(BaseQueueTask):
    song_id: int
    source_format: str
    target_format: str
```

---

### Task 3: Create RedisClient and Queue Logger

**Files:**
- Create: `rivo_drome/client/redis_client.py`
- Create: `rivo_drome/logger/queue_logger.py`
- Modify: `rivo_drome/container/default_container.py`

**Interfaces:**
- Produces: `RedisClient`, `QueueLogger`.

- [ ] **Step 1: Create QueueLogger**
```python
import logging

class QueueLogger:
    def __init__(self):
        self.logger = logging.getLogger("queue")
        # Add basic stdout handler if not already present

    def info(self, msg: str, *args):
        self.logger.info(msg, *args)
    
    def error(self, msg: str, *args):
        self.logger.error(msg, *args)
```

- [ ] **Step 2: Create RedisClient**
```python
import redis
from injector import inject

class RedisClient:
    @inject
    def __init__(self, host: str = "redis", port: int = 6379, password: str = ""):
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)

    def get_client(self) -> redis.Redis:
        return self.client
```

- [ ] **Step 3: Bind in DI Container**
In `rivo_drome/container/default_container.py`, read redis env vars and bind `RedisClient` and `QueueLogger`.

---

### Task 4: Create Queue Manager

**Files:**
- Create: `rivo_drome/manager/queue_manager.py`
- Create: `tests/manager/test_queue_manager.py`

**Interfaces:**
- Consumes: `RedisClient`, `QueueLogger`, Queue Models.
- Produces: `QueueManager` with `enqueue_task`, `dequeue_task`, `complete_task`, `clear_stale_tasks`.

- [ ] **Step 1: Write QueueManager**
Implement the manager using `redis_client.get_client().pipeline()`.
For `enqueue_task`: check if `task_id` in `processing:<queue_name>` (ZSET). If not, pipeline: `zadd` with current timestamp, and `rpush` to `queue:<queue_name>`.
For `dequeue_task`: `lpop`.
For `complete_task`: `zrem`.

- [ ] **Step 2: Write tests for QueueManager**
Write basic unit tests mocking `RedisClient`.

---

### Task 5: Create Cron Tasks

**Files:**
- Create: `rivo_drome/service/cron_task/base_cron_task.py`
- Create: `rivo_drome/service/cron_task/download_cron_task.py`

**Interfaces:**
- Consumes: `QueueManager`, `StreamService` (or `BaseDownloader`).

- [ ] **Step 1: Base Task**
```python
class BaseCronTask:
    def execute(self) -> None:
        raise NotImplementedError()
```

- [ ] **Step 2: Download Task**
Injected with `QueueManager` and `StreamService`. `execute()` tries to dequeue from `queue:download` using `DownloadTaskPayload`. If found, calls the actual download logic (extracted from `StreamService`) and then calls `complete_task`.

---

### Task 6: Cron CLI Command

**Files:**
- Create: `rivo_drome/command/cron_command.py`
- Modify: `rivo_drome/cli.py`

**Interfaces:**
- Consumes: `DownloadCronTask`.

- [ ] **Step 1: Write Cron loop**
Create `CronCommand` extending `AbstractCommand`. In `execute`, run a `while True:` loop calling `download_cron_task.execute()` and `time.sleep(1)`.

- [ ] **Step 2: Register in CLI**
Register `CronCommand` in `cli.py`.

---

### Task 7: Refactor StreamService and Controller

**Files:**
- Modify: `rivo_drome/service/stream_service.py`
- Modify: `rivo_drome/controller/audio_controller.py` (or equivalent API endpoint)

**Interfaces:**
- Consumes: `QueueManager`.

- [ ] **Step 1: Update StreamService**
Modify `stream_or_download` so that if the file is not found (and not on Navidrome), instead of calling `self._downloader.download(...)`, it creates a `DownloadTaskPayload` and calls `QueueManager.enqueue_task(...)`. Then it raises a specific exception or returns a flag indicating the task is queued.

- [ ] **Step 2: Update Controller**
Catch the new exception/flag and raise `HTTPException(status_code=404, detail="Audio in coda di download.")`.
