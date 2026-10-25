from abc import ABC, abstractmethod
from typing import Generic, Iterable, TypeVar

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection, ConnectionsFactory, L, Q

C = TypeVar('C', bound=AbstractChannel)

class QueueRepositoryInterface(ABC, Generic[Q]):
    """Generic in the class of queues it creates, loads and persists."""

    @abstractmethod
    def create(self) -> Q:
        """Creates a new queue. It is not persisted."""
        pass

    @abstractmethod
    def load(self, connection_id: str) -> Q:
        """Loads a queue given the connection id it belongs to."""
        pass

    @abstractmethod
    def persist(self, connection_id: str, queue: Q):
        """Persists queue and assign to connection."""
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        """Deletes a queue given the connection id it belongs to."""
        pass


class ListenerRepositoryInterface(ABC, Generic[L]):
    """Generic in the class of listeners it creates, loads and persists."""
    @abstractmethod
    def create(self) -> L:
        """Creates a new listener. It is not persisted."""
        pass

    @abstractmethod
    def load(self, connection_id: str) -> L:
        """Loads a listener given the connection id it belongs to."""
        pass

    @abstractmethod
    def persist(self, connection_id: str, listener: L):
        """Persists listener and assign to connection."""
        pass

    @abstractmethod
    def delete(self, connection_id: str):
        """Deleted a listener given the connection id it belongs to."""
        pass


class ConnectionRepositoryInterface(ConnectionsFactory, ABC):
    """
    Persists connections, and creates them using its listeners and queues repositories.

    Channel repositories inject it as **connections_factory** into the channels they build.
    """
    @property
    @abstractmethod
    def queues_repository(self) -> QueueRepositoryInterface:
        pass

    @property
    @abstractmethod
    def listeners_repository(self) -> ListenerRepositoryInterface:
        pass

    @abstractmethod
    def load_ids(self, channel_id: str) -> Iterable[str]:
        """Ids of the connections managed by a given channel, without loading their listeners and queues."""
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



class ChannelRepositoryInterface(ABC, Generic[C]):
    """Generic in the class of channels it handles."""
    @property
    @abstractmethod
    def connections_repository(self) -> ConnectionRepositoryInterface:
        """Repository to be used to persist connections. It is also the connections factory injected into the channels it builds."""
        pass

    @abstractmethod
    def load_all(self) -> Iterable[C]:
        """Loads all channels"""
        pass

    @abstractmethod
    def load_one(self, channel_id: str) -> C:
        """Loads a channel given its it"""
        pass

    @abstractmethod
    def persist(self, channel: C):
        """Persists a channel"""
        pass

    @abstractmethod
    def delete(self, channel_id: str):
        """Deletes a channel given its it"""
        pass

    @abstractmethod
    def create(self, channel_data: dict) -> C:
        """Creates a new channel and configures it depending on channel_data."""
        pass

