from abc import ABC, abstractmethod

import eric_sse
from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract
from eric_sse.queues import Queue, InMemoryQueue
from eric_sse.handlers import QueuingErrorHandler

class Connection:
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    def __init__(self, listener: MessageQueueListener, queue: Queue, connection_id: str | None = None):
        self.__listener = listener
        self.__queue = queue
        self.__id = connection_id or eric_sse.generate_uuid()
        self.__queues_error_handlers: list[QueuingErrorHandler] = []


    @property
    def listener(self) -> MessageQueueListener:
        return self.__listener

    @property
    def queue(self) -> Queue:
        return self.__queue

    @property
    def id(self) -> str:
        return self.__id

    def send_message(self, msg: MessageContract):
        try:
            self.__queue.push(msg)
        except Exception as e:
            for handler in self.__queues_error_handlers:
                handler.handle_push_error(msg=msg, exception=e)
            raise


    def fetch_message(self) -> MessageContract:
        try:
            return self.__queue.pop()
        except Exception as e:
            for handler in self.__queues_error_handlers:
                handler.handle_pop_error(exception=e)
            raise e

    def register_queuing_error_handler(self,  handler: QueuingErrorHandler):
        self.__queues_error_handlers.append(handler)


class ConnectionsFactory(ABC):
    @abstractmethod
    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        """
        Creates a connection

        :param ~eric_sse.listener.MessageQueueListener listener: If provided, assigns a concrete listener
        """
        pass


class InMemoryConnectionsFactory(ConnectionsFactory):
    """Creates Connections with In memory queues (no persistence support)"""
    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        if listener is None:
            listener = MessageQueueListener()
        return Connection(listener=listener, queue=InMemoryQueue())
