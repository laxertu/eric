from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import eric_sse
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue, InMemoryQueue

L = TypeVar('L', bound=MessageQueueListener)
Q = TypeVar('Q', bound=Queue)

class Connection(Generic[L, Q]):
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    def __init__(self, listener: L, queue: Q, connection_id: str | None = None):
        self.__listener = listener
        self.__queue = queue
        self.__id = connection_id or eric_sse.generate_uuid()

    @property
    def listener(self) -> L:
        return self.__listener

    @property
    def queue(self) -> Q:
        return self.__queue

    @property
    def id(self) -> str:
        return self.__id


class ConnectionsFactory(ABC, Generic[L, Q]):
    @abstractmethod
    def create(self, listener: L | None = None) -> Connection[L, Q]:
        """
        Creates a connection

        :param ~eric_sse.listener.MessageQueueListener listener: If provided, assigns a concrete listener
        """


class InMemoryConnectionsFactory(ConnectionsFactory[MessageQueueListener, InMemoryQueue]):
    """Creates Connections with In memory queues (no persistence support)"""
    def create(self, listener: MessageQueueListener | None = None) -> Connection[MessageQueueListener, InMemoryQueue]:
        if listener is None:
            listener = MessageQueueListener()
        return Connection(listener=listener, queue=InMemoryQueue())
