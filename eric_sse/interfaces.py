from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection, ConnectionsFactory
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue

class QueueRepositoryInterface(ABC):

    @abstractmethod
    def load(self, connection_id: str) -> Queue:
        """Loads a queue given the connection id it belongs to."""
        pass

    @abstractmethod
    def persist(self, connection_id: str, queue: Queue):
        """Persists queue and assign to connection."""
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
        """Persists listener and assign to connection."""
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
        """Loads all connections managed by a given channel"""
        pass

    @abstractmethod
    def load_one(self, channel_id: str, connection_id: str) -> Connection:
        """Loads a connection given the connection and channel id it belongs to."""
        pass

    @abstractmethod
    def persist(self, channel_id: str, connection: Connection):
        """Persists a connection and assign it to a channel."""
        pass

    @abstractmethod
    def delete(self, channel_id: str, connection_id: str):
        """Deletes a connection given the connection and channel id it belongs to."""
        pass



class ChannelRepositoryInterface(ABC):
    @property
    @abstractmethod
    def connections_factory(self) -> ConnectionsFactory:
        """The connections factory that will be injected into concrete channel instances."""
        pass

    @property
    @abstractmethod
    def connections_repository(self) -> ConnectionRepositoryInterface:
        """Repository to be used to persist connections."""
        pass

    @abstractmethod
    def load_all(self) -> Iterable[AbstractChannel]:
        """Loads all channels"""
        pass

    @abstractmethod
    def load_one(self, channel_id: str) -> AbstractChannel:
        """Loads a channel given its it"""
        pass

    @abstractmethod
    def persist(self, channel: AbstractChannel):
        """Persists a channel"""
        pass

    @abstractmethod
    def delete(self, channel_id: str):
        """Deletes a channel given its it"""
        pass

    @abstractmethod
    def create(self, channel_data: dict) -> AbstractChannel:
        """Creates a new channel and configures it depending on channel_data."""
        pass

