from eric_sse.handlers import QueuingErrorHandler
from eric_sse.message import MessageContract
from eric_sse.queues import Queue
from eric_sse import get_logger

logger = get_logger()

class DeadLetterQueueHandler(QueuingErrorHandler):
    def __init__(self, queue: Queue):
        self.__queue = queue

    def handle_push_error(self, msg: MessageContract, exception: Exception):
        try:
            self.__queue.push(msg)
        except Exception as  e:
            logger.exception(f"Dead-letter push failed. msg type: {msg.type} payload {msg.payload} {repr(e)}")


