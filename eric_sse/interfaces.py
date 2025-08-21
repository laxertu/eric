from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import AbstractQueue
# TODO add repos dependencies to connection one, improve builder

class ConnectionRepositoryInterface(ABC):

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

class QueueRepository(ABC):

    @abstractmethod
    def load(self, connection_id: str) -> AbstractQueue:
        pass

    @abstractmethod
    def persist(self, queue: AbstractQueue):
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        pass

class ListenerRepository(ABC):
    @abstractmethod
    def load(self, connection_id: str) -> MessageQueueListener:
        pass

    @abstractmethod
    def persist(self, listener: MessageQueueListener):
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        pass
