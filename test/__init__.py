import logging

import eric

def test_get_logger():
    logger = logging.getLogger()
    logger.handlers = []
    return logger

eric.get_logger = test_get_logger

