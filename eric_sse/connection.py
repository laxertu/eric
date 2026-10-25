from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

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


class DefaultConnectionsFactory(ConnectionsFactory[L, Q]):
    """
    Creates connections using given listener class and queue factory.

    :param listener_class: Class to instantiate when no listener is provided. Defaults to :class:`~eric_sse.listener.MessageQueueListener`.
    :param queue_factory: Called once per connection to create its queue. Defaults to :class:`~eric_sse.queues.InMemoryQueue`.
    """
    def __init__(
            self,
            listener_class: type[L] = MessageQueueListener,
            queue_factory: Callable[[], Q] = InMemoryQueue
    ):
        self.__listener_class = listener_class
        self.__queue_factory = queue_factory

    def create(self, listener: L | None = None) -> Connection[L, Q]:
        if listener is None:
            listener = self.__listener_class()
        return Connection(listener=listener, queue=self.__queue_factory())


class InMemoryConnectionsFactory(DefaultConnectionsFactory[MessageQueueListener, InMemoryQueue]):
    """Creates Connections with In memory queues (no persistence support)"""
