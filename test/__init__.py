import logging

import eric_sse


def test_get_logger():
    logger = logging.getLogger()
    logger.handlers = []
    return logger


eric_sse.get_logger = test_get_logger
