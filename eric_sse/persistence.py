"""
This module is intended to those who want to create their own persistence layer

A **Redis** concrete implementation of interfaces is available at  `eric-redis-queues package source <https://github.com/laxertu/eric-redis-queues/blob/master/eric_redis_queues/__init__.py>`_.

Here is a `Basic example <https://github.com/laxertu/eric/blob/master/examples/use_cases/basic.py>`_ of integration.

**Writing a custom persistence layer**

You'll need to implement the following interfaces:

**Channels**

* :class:`~eric_sse.persistence.ChannelRepositoryInterface`

* You'll need to define a channel that implements :class:`~eric_sse.persistence.PersistableChannel` if :class:`~eric_sse.prefabs.SSEChannel` do not suit with your requirements
* For **MessageQueueListener** support you can extend or directly use :class:`~eric_sse.persistence.PersistableListener`.

**Connections**

* :class:`~eric_sse.persistence.PersistableQueue`
* :class:`~eric_sse.persistence.ConnectionRepositoryInterface`
"""

from abc import ABC, abstractmethod
from typing import Iterable
from importlib import import_module

from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue, InMemoryQueue


class ObjectAsKeyValuePersistenceMixin(ABC):
    """
    Adds KV persistence support.

    By implementing this abstract mixin should be possible to persist every object that is not directly
    serializable by pickle, for example, if your Queues implementation wraps some incompatible dependency, e.g. a Redis client.

    For this reason, the idea is that dict values should be serializable by pickle too.

    see :func:`~eric_sse.persistence.importlib_create_instance`
    """
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
        """Does necessary post-creation setup of object given its persisted values"""
        ...

    @property
    def kv_class_absolute_path(self) -> str:
        """Returns class full path as string"""
        return f'{self.__module__}.{type(self).__name__}'

    @property
    @abstractmethod
    def kv_constructor_params_as_dict(self) -> dict:
        """Class constructor parameters as dict"""
        ...


def importlib_create_instance(class_full_path: str, constructor_params: dict, setup_values: dict) -> ObjectAsKeyValuePersistenceMixin:
    """
    Creates a persistable class instance given a persisted value and executes its setup_by_dict method

    see :func:`~eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.setup_by_dict`
    """
    path_parts = class_full_path.split('.')
    module = '.'.join(path_parts[:-1])
    klass = path_parts[-1]

    module_object = import_module(module)
    obj: ObjectAsKeyValuePersistenceMixin = getattr(module_object, klass)(constructor_params)
    obj.setup_by_dict(setup_values)

    return obj


class PersistableQueue(Queue, ObjectAsKeyValuePersistenceMixin, ABC):
    """Concrete implementations of methods should perform in **Queues** ones their I/O operations, and define in **ObjectAsKeyValuePersistenceMixin** ones their correspondant persistence strategy"""
    ...

class PersistableListener(MessageQueueListener, ObjectAsKeyValuePersistenceMixin):
    """Gives KV persistence support to MessageQueueListener."""
    @property
    def kv_key(self) -> str:
        return self.id

    @property
    def kv_value_as_dict(self) -> dict:
        return {}

    def setup_by_dict(self, setup: dict):
        pass

    @property
    def kv_constructor_params_as_dict(self) -> dict:
        return {}


class PersistableConnection(Connection):
    listener: PersistableListener
    queue: PersistableQueue

class PersistableChannel(ObjectAsKeyValuePersistenceMixin, ABC):
    ...

class ObjectRepositoryInterface(ABC):
    """Every exception raised by concrete implementations show be wrapped inside a :class:`~eric_sse.exception.RepositoryError`
    """

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
    def get_channel(self, channel_id: str) -> PersistableChannel:
        ...

    @abstractmethod
    def delete_listener(self, channel_id: str, listener_id: str) -> None:
        ...

class ConnectionRepositoryInterface(ABC):
    """
    Abstraction for connections creation.

    It exposes methods to be used by ChannelRepositoryInterface implementations for connections loading.

    see :class:`~eric_sse.entities.AbstractChannel`
    """

    @abstractmethod
    def create_queue(self, listener_id: str) -> Queue:
        """
        Returns a concrete Queue instance.

        :param str listener_id: Corresponding listener id
        """
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
        """Removes a persisted :class:`~eric_sse.persistence.PersistableConnection` given its correspondant listener id"""
        ...



class InMemoryConnectionRepository(ConnectionRepositoryInterface):
    """
    Default implementation used by :class:`~eric_sse.entities.AbstractChannel`
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
