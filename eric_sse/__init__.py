import logging
from logging import getLogger, StreamHandler, Logger


def get_logger() -> Logger:
    logger = getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(StreamHandler())

    return logger
