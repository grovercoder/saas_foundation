import logging
from logging.handlers import RotatingFileHandler
import os


class LogManager:
    _instance = None

    def __new__(
        cls,
        log_file="data/logs/application.log",
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
    ):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialize(log_file, max_bytes, backup_count)
        return cls._instance

    def _initialize(self, log_file, max_bytes, backup_count):
        self.logger = logging.getLogger("application_logger")
        self.logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File handler for rotating logs
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler for development (optional)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


# Example usage:
# log_manager = LogManager()
# logger = log_manager.get_logger()
# logger.info("This is an info message.")
# logger.error("This is an error message.")
