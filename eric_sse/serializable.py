"""
TODO refactor and delete this
"""

from typing import Iterable

from eric_sse.connection import Connection
from eric_sse.interfaces import ChannelRepositoryInterface, ListenerRepositoryInterface, QueueRepositoryInterface, \
    ConnectionRepositoryInterface
from eric_sse.persistence import KvStorageEngine

from eric_sse.entities import AbstractChannel
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue

class ListenerRepository(ListenerRepositoryInterface):

    def __init__(self, storage_engine: KvStorageEngine):
        self.__storage_engine = storage_engine

    def load(self, listener_id: str) -> MessageQueueListener:
        return self.__storage_engine.fetch_one(listener_id)

    def persist(self, listener: MessageQueueListener):
        self.__storage_engine.upsert(listener.id, listener)

    def delete(self, listener_id: str):
        self.__storage_engine.delete(listener_id)

class QueueRepository(QueueRepositoryInterface):
    def __init__(self, storage_engine: KvStorageEngine):
        self.__storage_engine = storage_engine

    def load(self, queue_id: str) -> Queue:
        return self.__storage_engine.fetch_one(queue_id)

    def persist(self, queue: Queue):
        self.__storage_engine.upsert(queue.id, queue)

    def delete(self, queue_id: str):
        self.__storage_engine.delete(queue_id)

class ConnectionRepository(ConnectionRepositoryInterface):

    def __init__(
            self,
            storage_engine: KvStorageEngine,
    ):
        self.__storage_engine = storage_engine

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for obj in self.__storage_engine.fetch_all():
            yield obj

    def load_one(self, connection_id: str) -> Connection:
        return self.__storage_engine.fetch_one(connection_id)

    def persist(self, connection: Connection):
        self.__storage_engine.upsert(connection.id, connection)

    def delete(self, connection_id: str):
        self.__storage_engine.delete(connection_id)


class ChannelRepository(ChannelRepositoryInterface):
    def __init__(self, storage_engine: KvStorageEngine, connection_repository: ConnectionRepositoryInterface):
        self.__storage_engine = storage_engine
        self.__connection_repository = connection_repository

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connection_repository

    def load_all(self) -> Iterable[AbstractChannel]:
        for channel in self.__storage_engine.fetch_all():
            yield self.load_one(channel.id)

    def load_one(self, channel_id: str) -> AbstractChannel:
        channel: AbstractChannel = self.__storage_engine.fetch_one(channel_id)
        for connection in self.__connection_repository.load_all(channel.id):
            channel.register_connection(listener=connection.listener, queue=connection.queue)
        return channel

    def persist(self, channel: AbstractChannel):
        self.__storage_engine.upsert(channel.id, channel)

    def delete(self, channel_id: str):
        self.__storage_engine.delete(channel_id)

