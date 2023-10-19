import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_log_handler(log_path: Path, formatter: logging.Formatter, rotate: bool = False) -> logging.Handler:
    """Setup logger with file handler."""
    if rotate:
        file_handler = RotatingFileHandler(log_path, maxBytes=2300000, backupCount=5)
    else:
        file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    return file_handler
