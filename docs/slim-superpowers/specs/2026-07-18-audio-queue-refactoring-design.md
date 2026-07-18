# Audio Queue Refactoring Design

## Overview
This document outlines the detailed refactoring of the audio download and conversion flows in `rivo-drome`. Currently, when an audio file is missing, the download process blocks the main API flow. The goal is to introduce an asynchronous task queue using Redis and a custom cron worker, ensuring the API responds instantly and heavy tasks (downloads, format conversions) are processed in the background.

## 1. Architecture & Infrastructure
- **Redis Service**: A `redis` container (e.g., `redis:7-alpine`) will be added to `docker-compose.yml` to store the task queues and processing states. We will mount a Docker volume (`redis_data`) to persist the queues across server restarts.
- **Cron Service**: A new `cron` container will be added to `docker-compose.yml`. It will run the same application image as the API (`proxy` service) but will execute a dedicated CLI command (`python -m rivo_drome.cli cron`) as its entrypoint. This completely separates web traffic from background processing.
- **Dependencies**: Add `redis` to `requirements.txt`.
- **Environment**: Add `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` to `.env` and load them in `rivo_drome/config/` (or via injector configuration).

## 2. Queue Manager & Anti-Duplication
We will create a robust Queue system using `redis-py` with atomic transactions (`pipeline`) to prevent race conditions.
- **Client**: `rivo_drome/client/redis_client.py` will wrap the `redis.Redis` connection.
- **Manager**: `rivo_drome/manager/queue_manager.py` will contain `QueueManager`.
  - **Queues**: Redis Lists (e.g., `queue:download`, `queue:convert`).
  - **Processing Trackers**: Redis ZSETs (Sorted Sets, e.g., `processing:download`) will track ongoing tasks with a timestamp as the score. This allows us to clear "stale/zombie" tasks if a worker crashes during execution.
  - **Methods**:
    - `enqueue_task(queue_name: str, task_id: str, payload: BaseModel) -> bool`: Checks if `task_id` is in the `processing` ZSET. If yes, returns `False` (skipped). If no, uses a Redis `pipeline` to atomically add the ID with the current timestamp to the ZSET, serialize the Pydantic `payload` to JSON, and push it to the List.
    - `dequeue_task(queue_name: str, model_class: type[BaseModel]) -> BaseModel | None`: Pops a task from the List, parses the JSON into `model_class`, and returns it.
    - `complete_task(queue_name: str, task_id: str)`: Removes `task_id` from the ZSET.
    - `clear_stale_tasks(queue_name: str, max_age_seconds: int)`: Removes items from the ZSET older than `max_age_seconds` to recover from worker crashes.

## 3. Queue Models
To ensure type safety and clean serialization/deserialization with Redis, we will define Pydantic models for the task payloads in `rivo_drome/model/queue_task.py`:
- `BaseQueueTask(BaseModel)`: Contains a `task_id` (str).
- `DownloadTaskPayload(BaseQueueTask)`: Contains fields needed for download (e.g., `song_id`, `artist`, `title`).
- `ConversionTaskPayload(BaseQueueTask)`: Contains fields needed for conversion (e.g., `song_id`, `source_format`, `target_format`).

## 3. Application Flow Changes
### Controller & Services (API Layer)
- We will modify the existing endpoint that requests an audio file (e.g., in `rivo_drome/controller/`).
- If the file is missing locally, instead of blocking for the download, the controller will create a `DownloadTaskPayload` and call `QueueManager.enqueue_task("queue:download", song_id, payload)`.
- The controller will immediately raise an HTTP 404 Exception (e.g., `HTTPException(status_code=404, detail="Audio non trovato, aggiunto in coda di download.")`).

### Cron Execution Loop & Tasks
- **CLI Command**: Add `@click.command("cron")` in `rivo_drome/command/cron.py` (and register it in `rivo_drome/cli.py`). The command will consist of an infinite `while True:` loop with a `time.sleep(1)` to avoid burning CPU cycles.
- **Task Organization**: We will create a new directory `rivo_drome/service/cron_task/` for specific tasks.
  - `DownloadCronTask`: Injected with `QueueManager` and `DownloadService`. Inside its `execute()` method, it attempts to `dequeue_task("queue:download")`. If a task is found, it processes the download. Upon completion/failure, calls `complete_task`.
  - `ConversionCronTask`: Similar logic, reading from `"queue:convert"` and delegating to the conversion service.
- The `cron` CLI loop will simply call `download_cron_task.execute()` and `conversion_cron_task.execute()` sequentially.

### Dependency Injection
- Update `rivo_drome/container/container.py` (`DefaultContainer._init_bindings`) to bind the new environment variables and allow implicit injection of `RedisClient`, `QueueManager`, and the new Cron Tasks.

### Logging
- Create `rivo_drome/logger/queue_logger.py` returning a pre-configured standard logger (`logging.getLogger("queue")`).
- This logger will trace `[ENQUEUE]`, `[DEQUEUE]`, `[PROCESSING_START]`, `[SUCCESS]`, and `[ERROR]` with task IDs and queue names, ensuring full traceability of background operations.
