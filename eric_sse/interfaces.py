from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue

class QueueRepositoryInterface(ABC):

    @abstractmethod
    def load(self, connection_id: str) -> Queue:
        """Loads a queue given the connection id it belongs to."""
        pass

    @abstractmethod
    def persist(self, connection_id: str, queue: Queue):
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        """Deletes a queue given the connection id it belongs to."""
        pass


class ListenerRepositoryInterface(ABC):
    @abstractmethod
    def load(self, connection_id: str) -> MessageQueueListener:
        """Loads a listener given the connection id it belongs to."""
        pass

    @abstractmethod
    def persist(self, connection_id: str, listener: MessageQueueListener):
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        """Deleted a listener given the connection id it belongs to."""
        pass


class ConnectionRepositoryInterface(ABC):
    @property
    @abstractmethod
    def queues_repository(self) -> QueueRepositoryInterface:
        pass

    @property
    @abstractmethod
    def listeners_repository(self) -> ListenerRepositoryInterface:
        pass

    @abstractmethod
    def load_all(self, channel_id: str) -> Iterable[Connection]:
        pass

    @abstractmethod
    def load_one(self, connection_id: str) -> Connection:
        pass

    @abstractmethod
    def persist(self, connection: Connection):
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        pass



class ChannelRepositoryInterface(ABC):
    @property
    @abstractmethod
    def connections_repository(self) -> ConnectionRepositoryInterface:
        pass

    @abstractmethod
    def load_all(self) -> Iterable[AbstractChannel]:
        pass

    @abstractmethod
    def load_one(self, channel_id: str) -> AbstractChannel:
        pass

    @abstractmethod
    def persist(self, channel: AbstractChannel):
        pass

    @abstractmethod
    def delete(self, channel_id: str):
        pass
