"""
This module is intended to those who want to create their own persistence layer.
A Redis implementation is available at https://pypi.org/project/eric-redis-queues/
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Any, AsyncIterable

from eric_sse.message import MessageContract
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

class ChannelInterface(ABC):

    @abstractmethod
    def open(self):
        ...

    @abstractmethod
    def add_listener(self) -> MessageQueueListener:
        ...

    @abstractmethod
    def register_listener(self, listener: MessageQueueListener):
        ...

    @abstractmethod
    def remove_listener(self, listener_id: str):
        ...

    @abstractmethod
    def dispatch(self, listener_id: str, msg: MessageContract):
        ...

    @abstractmethod
    def broadcast(self, msg: MessageContract):
        ...

    @abstractmethod
    def get_listener(self, listener_id: str) -> MessageQueueListener:
        ...

    @abstractmethod
    def adapt(self, msg: MessageContract) -> Any:
        ...

    @abstractmethod
    async def message_stream(self, listener: MessageQueueListener) -> AsyncIterable[Any]:
        ...

class ChannelRepositoryInterface(ABC):
    @abstractmethod
    def load(self) -> Iterable[ChannelInterface]:
        ...

    @abstractmethod
    def persist(self, channel: ChannelInterface):
        ...

    @abstractmethod
    def delete(self, channel_id: str):
        ...


class ConnectionRepositoryInterface(ABC):
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


class InMemoryConnectionRepository(ConnectionRepositoryInterface):
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
