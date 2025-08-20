from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.queues import Queue
from eric_sse.listener import MessageQueueListener

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

    # TODO dependency with conn repo

    @abstractmethod
    def load_one(self, channel_id: str) -> AbstractChannel:
        pass

    @abstractmethod
    def persist(self, channel: AbstractChannel):
        pass

    @abstractmethod
    def delete(self, channel_id: str):
        pass
