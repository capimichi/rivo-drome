import time
from injector import inject
from rivo_drome.command.abstract_command import AbstractCommand
from rivo_drome.service.cron_task.download_cron_task import DownloadCronTask

class CronCommand(AbstractCommand):
    command_name = "cron"

    @inject
    def __init__(self, download_cron_task: DownloadCronTask):
        self.download_cron_task = download_cron_task

    def run(self, **kwargs):
        print("Starting cron loop...")
        while True:
            self.download_cron_task.execute()
            time.sleep(1)
