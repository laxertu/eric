"""
This module is intended to those who want to create their own persistence layer.
A Redis implementation is available at https://pypi.org/project/eric-redis-queues/
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from eric_sse.listener import MessageQueueListener
from eric_sse.queue import Queue, InMemoryQueue


@dataclass
class Connection:
    """
    A connection is just a listener and its related message queue

    :param eric_sse.listener.MessageQueueListener listener:
    :param eric_sse.queue.Queue queue:
    """
    listener: MessageQueueListener
    queue: Queue


class AbstractConnectionRepository(ABC):
    """
    Abstraction for connections creation

    see :class:`eric_sse.entities.AbstractChannel`
    """
    @abstractmethod
    def create_queue(self, listener_id: str) -> Queue:
        """Returns a concrete :class:`eric_sse.connection.Connection`"""
        ...

    @abstractmethod
    def persist(self, connection: Connection) -> None:
        """Persists a concrete :class:`eric_sse.connection.Connection`"""
        ...

    @abstractmethod
    def load(self) -> Iterable[Connection]:
        """Returns an Iterable of all persisted connections :class:`eric_sse.connection.Connection`"""
        ...

    @abstractmethod
    def delete(self, listener_id: str) -> None:
        """Removes a persisted :class:`eric_sse.connection.Connection` given its correspondant listener id"""
        ...


class InMemoryConnectionRepository(AbstractConnectionRepository):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    def create_queue(self, listener_id: str) -> Queue:
        return InMemoryQueue()

    def persist(self, connection: Connection) -> None:
        pass

    def load(self) ->  Iterable[Connection]:
        return []

    def delete(self, listener_id: str) -> None:
        pass
