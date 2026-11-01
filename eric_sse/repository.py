from typing import Iterable, Generic, TypeVar, Callable
from abc import ABC, abstractmethod

from eric_sse.connection import Connection, L, Q
from eric_sse.entities import AbstractChannel
from eric_sse.exception import ItemNotFound
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import InMemoryQueue
from eric_sse.interfaces import ChannelRepositoryInterface, ConnectionRepositoryInterface, ListenerRepositoryInterface, \
    QueueRepositoryInterface

T = TypeVar('T')


class KvStorage(ABC, Generic[T]):
    """Represents a Key Value storage engine. Provides functionalities do load, persist and find by key prefix"""

    @abstractmethod
    def fetch_by_prefix(self, prefix: str) -> Iterable[T]:
        """
        Search by KV prefix

        Implementations must tolerate deletions of fetched keys while the result is being iterated.
        """
        pass

    @abstractmethod
    def fetch_all(self) -> Iterable[T]:
        """
        Return all items that have been persisted

        Implementations must tolerate deletions of fetched keys while the result is being iterated.
        """
        pass

    @abstractmethod
    def upsert(self, key: str, value: T):
        """Updates or inserts a value given its corresponding key"""
        pass

    @abstractmethod
    def fetch_one(self, key: str) -> T:
        """Return value correspondant to key"""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Idempotent deletion. Do not throw an error on invalid key"""
        pass


class InMemoryStorage(KvStorage[T]):
    """In memory implementation"""
    def __init__(self, items: dict[str, T] | None = None):
        self.items = items or {}

    def fetch_by_prefix(self, prefix: str) -> Iterable[T]:
        for k, obj in list(self.items.items()):
            if k.startswith(prefix):
                yield obj

    def fetch_all(self) -> Iterable[T]:
        for obj in list(self.items.values()):
            yield obj

    def upsert(self, key: str, value: T):
        self.items[key] = value

    def fetch_one(self, key: str) -> T:
        try:
            return self.items[key]
        except KeyError:
            raise ItemNotFound(key=key) from None

    def delete(self, key: str):
        if key not in self.items:
            return
        del self.items[key]

class PrefixedStorage(KvStorage[T]):
    """
    A namespaced view of another :class:`~eric_sse.repository.KvStorage`. All keys are prefixed with **prefix**.

    Allows several repositories to share a single storage instance.
    Prefixes of storages sharing the same instance must not be prefixes of each other.
    """
    def __init__(self, storage: KvStorage, prefix: str):
        self.__storage = storage
        self.__prefix = prefix

    def fetch_by_prefix(self, prefix: str) -> Iterable[T]:
        return self.__storage.fetch_by_prefix(f'{self.__prefix}{prefix}')

    def fetch_all(self) -> Iterable[T]:
        return self.__storage.fetch_by_prefix(self.__prefix)

    def upsert(self, key: str, value: T):
        self.__storage.upsert(f'{self.__prefix}{key}', value)

    def fetch_one(self, key: str) -> T:
        return self.__storage.fetch_one(f'{self.__prefix}{key}')

    def delete(self, key: str):
        self.__storage.delete(f'{self.__prefix}{key}')


class KvListenerRepository(ListenerRepositoryInterface, Generic[L]):
    """
    Listener repository backed by a :class:`~eric_sse.repository.KvStorage`.

    Listeners are stored as they are, keyed by connection id; serialization, if needed, is up to the storage.

    :param storage:
    :param listener_class: Class of listeners created by :meth:`create`. Defaults to :class:`~eric_sse.listener.MessageQueueListener`.
    """
    def __init__(self, storage: KvStorage[L], listener_class: type[L] = MessageQueueListener):
        self.__storage = storage
        self.__listener_class = listener_class

    def create(self) -> L:
        return self.__listener_class()

    def load(self, connection_id: str) -> L:
        return self.__storage.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: L):
        self.__storage.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.__storage.delete(connection_id)


class KvQueueRepository(QueueRepositoryInterface, Generic[Q]):
    """
    Queue repository backed by a :class:`~eric_sse.repository.KvStorage`.

    Queues are stored as they are, keyed by connection id; serialization, if needed, is up to the storage.

    Each queue class decides what of its state is serialised. A durable queue keeps its messages in its own
    backend and serialises only its identity and configuration (e.g. through ``__getstate__``), because
    messages are written by the queue itself on every push and pop.
    :class:`~eric_sse.queues.InMemoryQueue` can't be serialised: use it with a storage that keeps objects in process,
    such as :class:`~eric_sse.repository.InMemoryStorage`.

    :param storage:
    :param queue_factory: Called by :meth:`create` to create a queue. Defaults to :class:`~eric_sse.queues.InMemoryQueue`.
    """
    def __init__(self, storage: KvStorage[Q], queue_factory: Callable[[], Q] = InMemoryQueue):
        self.__storage = storage
        self.__queue_factory = queue_factory

    def create(self) -> Q:
        return self.__queue_factory()

    def load(self, connection_id: str) -> Q:
        return self.__storage.fetch_one(connection_id)

    def persist(self, connection_id: str, queue: Q):
        self.__storage.upsert(connection_id, queue)

    def delete(self, connection_id: str):
        self.__storage.delete(connection_id)


class ChannelRepository(ChannelRepositoryInterface):
    """
    Persists channels of a given class, using their :meth:`~eric_sse.entities.AbstractChannel.to_dict` and
    :meth:`~eric_sse.entities.AbstractChannel.from_dict` methods.

    Channels it builds get :attr:`connections_repository` as **connections_factory**,
    so that new connections are created by the persistence layer.

    :param storage: Storage for channels configuration.
    :param connections_repository:
    :param channel_class: Class of channels this repository creates, loads and persists, e.g. :class:`~eric_sse.prefabs.SSEChannel`.
    """
    def __init__(
            self,
            storage: KvStorage,
            connections_repository: ConnectionRepositoryInterface,
            channel_class: type[AbstractChannel]
    ):
        self.__storage = storage
        self.__connections_repository = connections_repository
        self.__channel_class = channel_class

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository

    @property
    def channel_class(self) -> type[AbstractChannel]:
        return self.__channel_class

    def create(self, channel_data: dict) -> AbstractChannel:
        """
        Creates a channel. It is not persisted.

        :param dict channel_data: Constructor parameters of **channel_class**, except **connections_factory**.
        """
        return self.__channel_class.from_dict(channel_data, connections_factory=self.__connections_repository)

    def _setup_channel(self, channel: AbstractChannel):
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            channel.register_connection(connection)
        return channel

    def load_all(self) -> Iterable[AbstractChannel]:
        for channel_data in self.__storage.fetch_all():
            channel = self.create(channel_data)
            for connection in self.__connections_repository.load_all(channel_id=channel.id):
                channel.register_connection(connection)
            yield channel

    def load_one(self, channel_id: str) -> AbstractChannel:
        channel = self.create(self.__storage.fetch_one(channel_id))
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            channel.register_connection(connection)
        return channel

    def persist(self, channel: AbstractChannel):
        """Persists channel configuration and its connections. Raises a TypeError if channel is not exactly of **channel_class**."""
        if type(channel) is not self.__channel_class:
            raise TypeError(f'{type(channel).__name__} channels cannot be persisted by a {self.__channel_class.__name__} repository')
        self.__storage.upsert(channel.id, channel.to_dict())

        persisted_connections_ids = {c.id for c in self.__connections_repository.load_all(channel_id=channel.id)}
        current_connections_ids = set()

        for connection in channel.get_connections():
            current_connections_ids.add(connection.id)
            self.__connections_repository.persist(channel_id=channel.id, connection=connection)

        for connection_id_to_remove in persisted_connections_ids - current_connections_ids:
            self.__connections_repository.delete(channel_id=channel.id, connection_id=connection_id_to_remove)

    def delete(self, channel_id: str):
        try:
            channel = self.load_one(channel_id)
        except ItemNotFound:
            return
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            self.__connections_repository.delete(channel_id=channel_id, connection_id=connection.id)
        self.__storage.delete(channel_id)

class ConnectionRepository(ConnectionRepositoryInterface):
    """
    Concrete Connection Repository

    Relies on :class:`~eric_sse.repository.KvStorage` abstraction for final writes of connections data, and on
    correspondant repositories for related objects ones.
    """
    def __init__(
            self,
            storage: KvStorage,
            listeners_repository: ListenerRepositoryInterface,
            queues_repository: QueueRepositoryInterface
    ):
        self.__storage = storage
        self.__listeners_repository = listeners_repository
        self.__queues_repository = queues_repository

    @property
    def queues_repository(self) -> QueueRepositoryInterface:
        return self.__queues_repository

    @property
    def listeners_repository(self) -> ListenerRepositoryInterface:
        return self.__listeners_repository

    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        """Creates a connection. Listener, if not provided, and queue are created by the corresponding repositories."""
        if listener is None:
            listener = self.__listeners_repository.create()
        return Connection(listener=listener, queue=self.__queues_repository.create())

    def _load_connection(self, connection_id: str) -> Connection:
        listener = self.__listeners_repository.load(connection_id=connection_id)
        queue = self.__queues_repository.load(connection_id=connection_id)

        return Connection(listener=listener, queue=queue, connection_id=connection_id)

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for connection_data in self.__storage.fetch_by_prefix(f'{channel_id}:'):
            yield self._load_connection(connection_data['id'])


    def load_one(self, channel_id: str, connection_id: str) -> Connection:
        return self._load_connection(self.__storage.fetch_one(f'{channel_id}:{connection_id}')['id'])

    def persist(self, channel_id: str, connection: Connection):
        self.__listeners_repository.persist(connection_id=connection.id, listener=connection.listener)
        self.__queues_repository.persist(connection_id=connection.id, queue=connection.queue)
        self.__storage.upsert(f'{channel_id}:{connection.id}', {'id': connection.id})

    def delete(self, channel_id: str, connection_id: str):
        self.__listeners_repository.delete(connection_id=connection_id)
        self.__queues_repository.delete(connection_id=connection_id)
        self.__storage.delete(key=f'{channel_id}:{connection_id}')

