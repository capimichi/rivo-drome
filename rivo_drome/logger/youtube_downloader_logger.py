from rivo_drome.logger.abstract_logger import AbstractLogger


class YoutubeDownloaderLogger(AbstractLogger):

    def __init__(self, log_dir: str):
        super().__init__(log_dir)

    def get_logger_name(self) -> str:
        return "youtube_downloader"
