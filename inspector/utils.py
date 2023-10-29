import configparser
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


def clean_up_log_handlers(logger: logging.Logger):
    """Clean up log handlers."""
    for handler in logger.handlers:
        if handler.__class__.__name__ == 'StreamHandler':
            continue
        logger.removeHandler(handler)
        handler.close()


def configure_logger(host: str) -> logging.Logger:
    config = configparser.ConfigParser()
    config.read('config.ini')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    logs_path = Path(config['logs']['logs_path']) / config['logs']['inspectors_log_path'] / f"inspector_{host}.log"
    log_file_handler = get_log_handler(logs_path, formatter, rotate=True)
    logger.addHandler(log_file_handler)

    return logger
