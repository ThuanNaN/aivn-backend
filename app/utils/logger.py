import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"

class Logger(logging.Logger):
    def __init__(self, name="", log_level=logging.INFO, log_file=None) -> None:
        super().__init__(name, log_level)
        self.get_logger(log_level, log_file)
    
    def get_logger(self, log_level, log_file):
        self.setLevel(log_level)
        self._init_formatter()
        if log_file is not None:
            self._add_file_handler(LOG_DIR / log_file)
        else:
            self._add_stream_handler()
    
    def _init_formatter(self):
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _add_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(self.formatter)
        self.addHandler(stream_handler)

    def _add_file_handler(self, log_file):
        file_handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=10)
        file_handler.setFormatter(self.formatter)
        self.addHandler(file_handler)