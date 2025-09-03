from typing import Iterable, Any
from abc import ABC, abstractmethod

from eric_sse.connection import Connection, ConnectionsFactory
from eric_sse.entities import AbstractChannel
from eric_sse.interfaces import ChannelRepositoryInterface, ConnectionRepositoryInterface, ListenerRepositoryInterface, \
    QueueRepositoryInterface
from eric_sse.exception import RepositoryError

class KvStorage(ABC):
    @abstractmethod
    def fetch_by_prefix(self, prefix: str) -> Iterable[Any]:
        pass

    @abstractmethod
    def fetch_all(self) -> Iterable[Any]:
        pass

    @abstractmethod
    def upsert(self, key: str, value: Any):
        pass

    @abstractmethod
    def fetch_one(self, key: str) -> Any:
        pass

    @abstractmethod
    def delete(self, key: str):
        pass


class InMemoryStorage(KvStorage):

    def __init__(self, items: dict[str, Any] = None):
        self.items = items or {}

    def fetch_by_prefix(self, prefix: str) -> Iterable[Any]:
        for k, obj in self.items.items():
            if k.startswith(prefix):
                yield obj

    def fetch_all(self) -> Iterable[Any]:
        for obj in self.items.values():
            yield obj

    def upsert(self, key: str, value: Any):
        self.items[key] = value

    def fetch_one(self, key: str) -> Any:
        try:
            return self.items[key]
        except KeyError:
            raise RepositoryError(f'Item not found {key}') from None

    def delete(self, key: str):
        del self.items[key]

class AbstractChannelRepository(ChannelRepositoryInterface, ABC):
    def __init__(
            self,
            storage: KvStorage,
            connections_repository: ConnectionRepositoryInterface,
            connections_factory: ConnectionsFactory
    ):
        self.__storage = storage
        self.__connections_repository = connections_repository
        self.__connections_factory = connections_factory

    @property
    def connections_factory(self) -> ConnectionsFactory:
        return self.__connections_factory

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository


    @staticmethod
    @abstractmethod
    def _channel_to_dict(channel: AbstractChannel) -> dict:
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
        for connection in channel.get_connections():
            self.__connections_repository.persist(channel_id=channel.id, connection=connection)

    def delete(self, channel_id: str):
        channel = self.load_one(channel_id)
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            self.__connections_repository.delete(channel_id=channel_id, connection_id=connection.id)
        self.__storage.delete(channel_id)

class ConnectionRepository(ConnectionRepositoryInterface):
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

