from typing import Iterable, Generic, TypeVar, Callable
from abc import ABC, abstractmethod

from eric_sse.connection import Connection, ConnectionsFactory, InMemoryConnectionsFactory
from eric_sse.entities import AbstractChannel
from eric_sse.exception import ItemNotFound
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue
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

class KvListenerRepository(ListenerRepositoryInterface):
    """
    Listener repository backed by a :class:`~eric_sse.repository.KvStorage`.

    Listeners are stored as they are, keyed by connection id; serialization, if needed, is up to the storage.
    """
    def __init__(self, storage: KvStorage[MessageQueueListener]):
        self.__storage = storage

    def load(self, connection_id: str) -> MessageQueueListener:
        return self.__storage.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: MessageQueueListener):
        self.__storage.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.__storage.delete(connection_id)


class KvQueueRepository(QueueRepositoryInterface):
    """
    Queue repository backed by a :class:`~eric_sse.repository.KvStorage`.

    Queues are stored as they are, keyed by connection id; serialization, if needed, is up to the storage.
    """
    def __init__(self, storage: KvStorage[Queue]):
        self.__storage = storage

    def load(self, connection_id: str) -> Queue:
        return self.__storage.fetch_one(connection_id)

    def persist(self, connection_id: str, queue: Queue):
        self.__storage.upsert(connection_id, queue)

    def delete(self, connection_id: str):
        self.__storage.delete(connection_id)


class AbstractChannelRepository(ChannelRepositoryInterface, ABC):
    """
    Abstract base class for channel repositories.

    Builds channels before return them using injected repositories
    """
    def __init__(
            self,
            storage: KvStorage,
            connections_repository: ConnectionRepositoryInterface,
            connections_factory: ConnectionsFactory
    ):
        self.__storage = storage
        self.__connections_repository = connections_repository
        self.__connections_factory = connections_factory

    @classmethod
    def from_storage(
            cls,
            storage_factory: Callable[[], KvStorage] = InMemoryStorage,
            connections_factory: ConnectionsFactory | None = None
    ):
        """
        Builds a fully wired repository, using a separate storage for channels, connections, listeners and queues.

        :param storage_factory: Called once per storage needed. Defaults to :class:`~eric_sse.repository.InMemoryStorage`.
        :param connections_factory: Defaults to :class:`~eric_sse.connection.InMemoryConnectionsFactory`.
        """
        return cls(
            storage=storage_factory(),
            connections_repository=ConnectionRepository(
                storage=storage_factory(),
                listeners_repository=KvListenerRepository(storage_factory()),
                queues_repository=KvQueueRepository(storage_factory())
            ),
            connections_factory=connections_factory or InMemoryConnectionsFactory()
        )

    @property
    def connections_factory(self) -> ConnectionsFactory:
        return self.__connections_factory

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository


    @staticmethod
    @abstractmethod
    def _channel_to_dict(channel: AbstractChannel) -> dict:
        """
        Returns a dictionary representation of the channel to be passed to :meth:`eric_sse.interfaces.ChannelRepositoryInterface.create` calls.
        """
        pass

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
        self.__storage.upsert(channel.id, self._channel_to_dict(channel))

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

    def _load_connection(self, connection_id: str) -> Connection:
        listener = self.__listeners_repository.load(connection_id=connection_id)
        queue = self.__queues_repository.load(connection_id=connection_id)

        return Connection(listener=listener, queue=queue, connection_id=connection_id)

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for connection_data in self.__storage.fetch_by_prefix(channel_id):
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

