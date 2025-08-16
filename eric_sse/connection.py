from abc import ABC, abstractmethod

import eric_sse
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue, InMemoryQueue


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

    @property
    def listener(self) -> MessageQueueListener:
        return self.__listener

    @property
    def queue(self) -> Queue:
        return self.__queue

    @property
    def id(self) -> str:
        return self.__id


class ConnectionsFactory(ABC):
    @abstractmethod
    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        pass


class InMemoryConnectionsFactory(ConnectionsFactory):

    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        if listener is None:
            listener = MessageQueueListener()
        return Connection(listener=listener, queue=InMemoryQueue())
