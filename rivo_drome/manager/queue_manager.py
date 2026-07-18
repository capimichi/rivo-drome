import time
from typing import Optional, Type, TypeVar
from injector import inject
from rivo_drome.client.redis_client import RedisClient
from rivo_drome.logger.queue_logger import QueueLogger
from rivo_drome.model.queue_task import BaseQueueTask

T = TypeVar('T', bound=BaseQueueTask)

class QueueManager:
    @inject
    def __init__(self, redis_client: RedisClient, logger: QueueLogger):
        self.redis = redis_client.get_client()
        self.logger = logger

    def enqueue_task(self, queue_name: str, task: BaseQueueTask) -> bool:
        task_id = task.task_id
        processing_key = f"processing:{queue_name}"
        queue_key = f"queue:{queue_name}"
        
        if self.redis.zscore(processing_key, task_id) is not None:
            self.logger.info(f"Task {task_id} is already processing in {queue_name}")
            return False
            
        pipeline = self.redis.pipeline()
        pipeline.zadd(processing_key, {task_id: time.time()})
        pipeline.rpush(queue_key, task.model_dump_json())
        pipeline.execute()
        
        self.logger.info(f"Enqueued task {task_id} to {queue_name}")
        return True

    def dequeue_task(self, queue_name: str, task_model: Type[T]) -> Optional[T]:
        queue_key = f"queue:{queue_name}"
        task_json = self.redis.lpop(queue_key)
        
        if not task_json:
            return None
            
        try:
            task = task_model.model_validate_json(task_json)
            processing_key = f"processing:{queue_name}"
            self.redis.zadd(processing_key, {task.task_id: time.time()})
            return task
        except Exception as e:
            self.logger.error(f"Failed to parse task from {queue_name}: {e}")
            return None

    def complete_task(self, queue_name: str, task_id: str) -> None:
        processing_key = f"processing:{queue_name}"
        self.redis.zrem(processing_key, task_id)
        self.logger.info(f"Completed task {task_id} in {queue_name}")

    def clear_stale_tasks(self, queue_name: str, timeout_seconds: int = 3600) -> None:
        processing_key = f"processing:{queue_name}"
        cutoff = time.time() - timeout_seconds
        stale_tasks = self.redis.zrangebyscore(processing_key, 0, cutoff)
        if stale_tasks:
            self.redis.zremrangebyscore(processing_key, 0, cutoff)
            self.logger.info(f"Cleared {len(stale_tasks)} stale tasks from {queue_name}")
