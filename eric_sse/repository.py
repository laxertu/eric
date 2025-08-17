from abc import ABC, abstractmethod
from typing import Iterable
from eric_sse.interfaces import ChannelRepositoryInterface, ConnectionRepositoryInterface, ListenerRepositoryInterface, \
    QueueRepositoryInterface

from eric_sse.persistence import KvStorageEngine, ObjectAsKeyValuePersistenceMixin
from eric_sse.channel import PersistableChannel
from eric_sse.connection import Connection

class ChannelStorageEngine(KvStorageEngine, ABC):

    @abstractmethod
    def fetch_all(self) -> Iterable[PersistableChannel]:
        pass

    @abstractmethod
    def upsert(self, key: str, value: PersistableChannel):
        pass

    @abstractmethod
    def fetch_one(self, key: str) -> PersistableChannel:
        pass

    @abstractmethod
    def delete(self, key: str):
        pass


class ConnectionStorageEngine(KvStorageEngine, ABC):

    @abstractmethod
    def fetch_by_channel_id(self, channel_id: str) -> Iterable[Connection]:
        pass

class AbstractPersistableChannelRepository(ChannelRepositoryInterface, ABC):


    def __init__(self, storage_engine: KvStorageEngine, connections_repository: ConnectionRepositoryInterface):
        self._storage_engine = storage_engine
        self.__connections_repository = connections_repository

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository

    @abstractmethod
    def create_instance(self, persisted_kv: ObjectAsKeyValuePersistenceMixin) -> PersistableChannel:
        pass

    def load_all(self) -> Iterable[PersistableChannel]:
        for channel_kv in self._storage_engine.fetch_all():
            channel = self.create_instance(channel_kv)
            for connection in self.__connections_repository.load_all(channel_id=channel.kv_key):
                channel.register_connection(
                    listener=connection.listener,
                    queue=connection.queue
                )
            yield channel

    def load_one(self, channel_id: str) -> PersistableChannel:
        channel = self._storage_engine.fetch_one(channel_id)
        for connection in self.__connections_repository.load_all(channel_id=channel_id):
            channel.register_connection(
                listener=connection.listener,
                queue=connection.queue
            )
        return channel


    def persist(self, channel: PersistableChannel):
        self._storage_engine.upsert(channel.kv_key, channel.kv_as_dict)

    def delete(self, channel_id: str):
        self._storage_engine.delete(channel_id)

class AbstractConnectionRepository(ConnectionRepositoryInterface, ABC):
    def __init__(
            self,
            storage_engine: ConnectionStorageEngine,
            listeners_repository: ListenerRepositoryInterface,
            queues_repository: QueueRepositoryInterface,
    ):
        self._storage_engine = storage_engine
        self._listeners_repository = listeners_repository
        self._queues_repository = queues_repository

    @abstractmethod
    def create_connection_instance(self, kv_stored: ObjectAsKeyValuePersistenceMixin) -> Connection:
        pass

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for kv_stored in self._storage_engine.fetch_by_channel_id(channel_id=channel_id):
            yield self.create_connection_instance(kv_stored)

    def load_one(self, connection_id: str) -> Connection:
        return self.create_connection_instance(self._storage_engine.fetch_one(connection_id))

    def persist(self, connection: Connection):
        self._storage_engine.upsert(connection.kv_key, connection.kv_as_dict)

    def delete(self, connection_id: str):
        self._storage_engine.delete(connection_id)
