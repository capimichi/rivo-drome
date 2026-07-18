import asyncio
from injector import inject
from rivo_drome.manager.queue_manager import QueueManager
from rivo_drome.service.cron_task.base_cron_task import BaseCronTask
from rivo_drome.model.queue_task import DownloadTaskPayload
from rivo_drome.service.stream_service import StreamService

class DownloadCronTask(BaseCronTask):
    @inject
    def __init__(self, queue_manager: QueueManager, stream_service: StreamService):
        self.queue_manager = queue_manager
        self.stream_service = stream_service

    def execute(self) -> None:
        task = self.queue_manager.dequeue_task("download", DownloadTaskPayload)
        if task:
            try:
                self.queue_manager.logger.info(f"Cron processing download task {task.task_id} for {task.artist_name} - {task.title}")
                # We extract the actual downloading logic into process_download
                asyncio.run(self.stream_service.process_download(task.song_id))
            except Exception as e:
                self.queue_manager.logger.error(f"Error executing download task {task.task_id}: {e}")
            finally:
                self.queue_manager.complete_task("download", task.task_id)
