from eric_sse.handlers import QueuingErrorHandler
from eric_sse.interfaces import QueueRepositoryInterface
from eric_sse.message import MessageContract
from eric_sse.queues import Queue
from eric_sse import get_logger

logger = get_logger()

class DeadLetterQueueHandler(QueuingErrorHandler):
    def __init__(self, queue: Queue):
        self.__queue = queue

    @property
    def queue(self) -> Queue:
        return self.__queue

    def handle_push_error(self, msg: MessageContract, exception: Exception):
        try:
            self.__queue.push(msg)
        except Exception as  e:
            logger.exception(f"Dead-letter push failed. msg type: {msg.type} payload {msg.payload} {repr(e)}")

class DeadLetterQueueRepository:
    def __init__(self, queue_repository: QueueRepositoryInterface):
        self.__queue_repository = queue_repository

    def persist(self, connection_id: str, handler: DeadLetterQueueHandler):
        self.__queue_repository.persist(connection_id, handler.queue)
