from abc import ABC, abstractmethod
from typing import Iterable, Any

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
    def connections_factory(self) -> ConnectionsFactory:
        pass

    @abstractmethod
    def load_all(self, channel_id: str) -> Iterable[Connection]:
        """Loads all connections managed by a given channel"""
        pass

    @abstractmethod
    def load_one(self, connection_id: str) -> Connection:
        """Loads a connection given the connection and channel id it belongs to."""
        pass

    @abstractmethod
    def persist(self, channel_id: str, connection: Connection):
        """Persists a connection and assign it to a channel."""
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        """Deletes a connection given its id."""
        pass


class KvStorageInterface(ABC):
    """Represents a Key Value storage engine. Provides functionalities do load, persist and find by key prefix"""

    @abstractmethod
    def fetch_by_prefix(self, prefix: str) -> Iterable[Any]:
        """Search by KV prefix"""
        pass

    @abstractmethod
    def fetch_all(self) -> Iterable[Any]:
        """Return all items that have been persisted"""
        pass

    @abstractmethod
    def upsert(self, key: str, value: Any):
        """Updates or inserts a value given its corresponding key"""
        pass

    @abstractmethod
    def fetch_one(self, key: str) -> Any:
        """Return value corresponding to key"""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Idempotent deletion. Do not throw an error on invalid key"""
        pass
