import logging
from logging import getLogger, StreamHandler, Logger

def get_logger() -> Logger:
    logger = getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(StreamHandler())

    return logger
