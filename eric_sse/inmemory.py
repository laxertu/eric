from typing import Iterable
from abc import ABC
from eric_sse.interfaces import ConnectionRepositoryInterface, ChannelRepositoryInterface, ListenerRepositoryInterface, \
    QueueRepositoryInterface
from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.exception import RepositoryError
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue


class InMemoryStorage:

    def __init__(self, objects: dict[str, any] = None):
        self.objects = objects or {}

    objects: dict[str, any] = {}

    def fetch_by_prefix(self, prefix: str) -> Iterable[any]:
        for k, obj in self.objects.items():
            if k.startswith(prefix):
                yield obj

    def fetch_all(self) -> Iterable[any]:
        for obj in self.objects.values():
            yield obj

    def upsert(self, key: str, value: any):
        self.objects[key] = value

    def fetch_one(self, key: str) -> any:
        try:
            return self.objects[key]
        except KeyError:
            raise RepositoryError(f'Item not found {key}') from None

    def delete(self, key: str):
        del self.objects[key]

class InMemoryRepositoryMixin(ABC):
    def __init__(self):
        self.objects = InMemoryStorage()


class InMemoryQueueRepository(InMemoryRepositoryMixin, QueueRepositoryInterface):

    def load(self, connection_id: str) -> Queue:
        return self.objects.fetch_one(connection_id)

    def persist(self, connection_id: str, queue: Queue):
        self.objects.upsert(connection_id, queue)

    def delete(self, connection_id: str):
        self.objects.delete(connection_id)


class InMemoryListenerRepository(InMemoryRepositoryMixin, ListenerRepositoryInterface):

    def load(self, connection_id: str) -> MessageQueueListener:
        return self.objects.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: MessageQueueListener):
        self.objects.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.objects.delete(connection_id)


class InMemoryConnectionRepository(InMemoryRepositoryMixin, ConnectionRepositoryInterface):
    def __init__(self):
        super().__init__()
        self.__queues_repository = InMemoryQueueRepository()
        self.__listeners_repository = InMemoryListenerRepository()

    @property
    def queues_repository(self) -> QueueRepositoryInterface:
        return self.__queues_repository

    @property
    def listeners_repository(self) -> ListenerRepositoryInterface:
        return self.__listeners_repository

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for connection in self.objects.fetch_all():
            yield connection

    def load_one(self, connection_id: str) -> Connection:
        return self.objects.fetch_one(connection_id)

    def persist(self, connection: Connection):
        self.objects.upsert(connection.id, connection)

    def delete(self, connection_id: str):
        self.objects.delete(connection_id)


class InMemoryChannelRepository(InMemoryRepositoryMixin, ChannelRepositoryInterface):
    def __init__(self, channels: list[AbstractChannel] = None):
        super().__init__()
        for channel in channels or []:
            self.objects.upsert(channel.id, channel)
        self.__connections_repository = InMemoryConnectionRepository()

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository

    def load_all(self) -> Iterable[AbstractChannel]:
        for channel in self.objects.fetch_all():
            yield channel

    def load_one(self, channel_id: str) -> AbstractChannel:
        try:
            return self.objects.fetch_one(channel_id)
        except KeyError:
            raise RepositoryError(f'Item not found {channel_id}') from None

    def persist(self, channel: AbstractChannel):
        self.objects.upsert(channel.id, channel)

    def delete(self, channel_id: str):
        self.objects.delete(channel_id)



