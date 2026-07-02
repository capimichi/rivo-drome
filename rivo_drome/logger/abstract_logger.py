import logging
import os
from abc import ABC, abstractmethod


class AbstractLogger(ABC):
    """Base class for dedicated loggers writing to specific files in var/log."""

    def __init__(self, log_dir: str):
        self.logger_name = self.get_logger_name()
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            log_filename = f"{self.logger_name}.log"
            log_path = os.path.join(log_dir, log_filename)

            handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @abstractmethod
    def get_logger_name(self) -> str:
        """Returns the logger name, which is also used as the file name (e.g. 'proxy' for proxy.log)."""
        pass
