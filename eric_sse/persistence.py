"""
This module is intended to those who want to create their own persistence layer

A **Redis** concrete implementation of interfaces is available at  `eric-redis-queues package source <https://github.com/laxertu/eric-redis-queues/blob/master/eric_redis_queues/__init__.py>`_.

**Writing a custom persistence layer**

You need to implement the following interfaces:

**Channels**

* :class:`eric_sse.persistence.ChannelRepositoryInterface`

* You'll need to define a channel that implements :class:`eric_sse.persistence.ObjectAsKeyValuePersistenceMixin` if :class:`eric_sse.prefabs.SSEChannel` do not suit with your requirements


**Connections**

* :class:`eric_sse.persistence.PersistableQueue`
* :class:`eric_sse.persistence.ConnectionRepositoryInterface`

"""

from abc import ABC, abstractmethod
from typing import Iterable

from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
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


class PersistableQueue(Queue, ObjectAsKeyValuePersistenceMixin, ABC):
    """Concrete implementations of methods should perform in **Queues** ones their I/O operations, and define in **ObjectAsKeyValuePersistenceMixin** ones their correspondant persistence strategy"""
    ...

class PersistableListener(MessageQueueListener, ObjectAsKeyValuePersistenceMixin):

    @property
    def kv_key(self) -> str:
        return self.id

    @property
    def kv_value_as_dict(self) -> dict:
        return {}

    def setup_by_dict(self, setup: dict):
        pass


class PersistableConnection(Connection):
    listener: PersistableListener
    queue: PersistableQueue

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
    Abstraction for connections creation.

    It exposes methods to be used by ChannelRepositoryInterface implementations for connections loading.

    see :class:`eric_sse.entities.AbstractChannel`
    """

    @abstractmethod
    def create_queue(self, listener_id: str) -> Queue:
        """Returns a concrete Queue instance."""
        ...

    @abstractmethod
    def persist(self, channel_id: str, connection: PersistableConnection) -> None:
        ...

    @abstractmethod
    def load_all(self) -> Iterable[PersistableConnection]:
        """Returns an Iterable of all persisted connections"""
        ...

    @abstractmethod
    def load(self, channel_id: str) -> Iterable[PersistableConnection]:
        """Returns an Iterable of all persisted connections of a given channel"""
        ...

    @abstractmethod
    def delete(self, channel_id: str, listener_id: str) -> None:
        """Removes a persisted :class:`eric_sse.connection.PersistableConnection` given its correspondant listener id"""
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
        return []

    def delete(self, channel_id: str, listener_id: str) -> None:
        pass
