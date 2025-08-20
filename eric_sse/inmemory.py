from typing import Iterable

from eric_sse.interfaces import ConnectionRepositoryInterface, ChannelRepositoryInterface, QueueRepositoryInterface, \
    ListenerRepositoryInterface
from eric_sse.listener import MessageQueueListener
from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.queues import Queue
from eric_sse.exception import RepositoryError

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

class InMemoryConnectionRepository(ConnectionRepositoryInterface):
    def __init__(
        self,
        connections: dict[str, Connection] = None
    ):
        self.connections = connections or {}

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        pass

    def load_one(self, connection_id: str) -> Connection:
        pass

    def persist(self, connection: Connection):
        pass

    def delete(self, connection_id: str):
        pass


class InMemoryChannelRepository(ChannelRepositoryInterface):
    def __init__(
            self,
            connections_repository: ConnectionRepositoryInterface,
            channels: dict[str, AbstractChannel] = None
    ):
        self.__connections_repository = connections_repository

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository

    def load_all(self) -> Iterable[AbstractChannel]:
        pass

    def load_one(self, channel_id: str) -> AbstractChannel:
        pass

    def persist(self, channel: AbstractChannel):
        pass

    def delete(self, channel_id: str):
        pass


class InMemoryQueueRepository(QueueRepositoryInterface):
    def __init__(self, queues: dict[str, Queue] = None):
        self.__queues = queues or {}

    def load(self, queue_id: str) -> Queue:
        pass

    def persist(self, queue: Queue):
        pass

    def delete(self, queue_id: str):
        pass


class InMemoryListenerRepository(ListenerRepositoryInterface):
    def __init__(self, listeners: dict[str, MessageQueueListener] = None):
        self.__listeners = listeners or {}

    def load(self, listener_id: str) -> MessageQueueListener:
        pass

    def persist(self, listener: MessageQueueListener):
        pass

    def delete(self, listener_id: str):
        pass


