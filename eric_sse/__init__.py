import logging
from logging import getLogger, StreamHandler, Logger
from uuid import uuid4

def get_logger() -> Logger:
    logger = getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt='[%(asctime)s][ERIC][%(levelname)s]%(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler = StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def generate_uuid() -> str:
    return str(uuid4())
