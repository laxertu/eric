"""
This module is intended to those who want to create their own persistence layer.
A Redis implementation is available at https://pypi.org/project/eric-redis-queues/
"""

from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.connection import Connection
from eric_sse.queues import Queue, InMemoryQueue


class ObjectAsKeyValuePersistenceMixin(ABC):
    """Adds KV persistence support."""
    @property
    @abstractmethod
    def kv_key(self) -> str:
        """The key to use when persisting object"""
        ...

    @property
    @abstractmethod
    def kv_value_as_dict(self) -> dict:
        """Returns value that will be persisted as a dictionary."""
        ...

    @abstractmethod
    def setup_by_dict(self, setup: dict):
        """Does de necessary setup of object given its persisted values"""
        ...


class ObjectRepositoryInterface(ABC):

    @abstractmethod
    def load(self) -> Iterable[ObjectAsKeyValuePersistenceMixin]:
        """Returns an Iterable of all persisted objects of correspondant concrete implementation."""
        ...

    @abstractmethod
    def persist(self, persistable: ObjectAsKeyValuePersistenceMixin):
        ...

    @abstractmethod
    def delete(self, key: str):
        ...


class ChannelRepositoryInterface(ObjectRepositoryInterface):

    @abstractmethod
    def delete_listener(self, channel_id: str, listener_id: str) -> None:
        ...

class ConnectionRepositoryInterface(ABC):
    """
    Abstraction for connections creation

    see :class:`eric_sse.entities.AbstractChannel`
    """

    @abstractmethod
    def create_queue(self, listener_id: str) -> Queue:
        """Returns a concrete Queue instance."""
        ...

    @abstractmethod
    def persist(self, channel_id: str, connection: Connection) -> None:
        ...

    @abstractmethod
    def load_all(self) -> Iterable[Connection]:
        """Returns an Iterable of all persisted connections"""
        ...
    @abstractmethod
    def load(self, channel_id: str) -> Iterable[Connection]:
        """Returns an Iterable of all persisted connections of a given channel"""
        ...

    @abstractmethod
    def delete(self, channel_id: str, listener_id: str) -> None:
        """Removes a persisted :class:`eric_sse.connection.Connection` given its correspondant listener id"""
        ...



class InMemoryConnectionRepository(ConnectionRepositoryInterface):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    def create_queue(self, listener_id: str) -> Queue:
        return InMemoryQueue()

    def persist(self, channel_id: str, connection: Connection) -> None:
        pass

    def load_all(self) ->  Iterable[Connection]:
        return []

    def load(self, channel_id: str) -> Iterable[Connection]:
        pass

    def delete(self, channel_id: str, listener_id: str) -> None:
        pass
