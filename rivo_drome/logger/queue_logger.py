import logging

class QueueLogger:
    def __init__(self):
        self.logger = logging.getLogger("queue")
        # Add basic stdout handler if not already present
        if not self.logger.hasHandlers():
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def info(self, msg: str, *args):
        self.logger.info(msg, *args)
    
    def error(self, msg: str, *args):
        self.logger.error(msg, *args)
