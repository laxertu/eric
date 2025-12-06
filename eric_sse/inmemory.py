from typing import Any, Iterable

from eric_sse.connection import InMemoryConnectionsFactory, ConnectionsFactory, Connection
from eric_sse.exception import ItemNotFound
from eric_sse.interfaces import ConnectionRepositoryInterface, QueueRepositoryInterface, ListenerRepositoryInterface, \
    KvStorageInterface
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import InMemoryQueue


class InMemoryStorage(KvStorageInterface):
    """In memory implementation"""
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
            raise ItemNotFound(key=key) from None

    def delete(self, key: str):
        if key not in self.items:
            return
        del self.items[key]


class InMemoryConnectionRepository(ConnectionRepositoryInterface):
    def __init__(self):
        self.__connections_factory = InMemoryConnectionsFactory()
        self.__queues_repository = InMemoryQueueRepository(InMemoryStorage())
        self.__listeners_repository = InMemoryListenerRepository(InMemoryStorage())

    @property
    def connections_factory(self) -> ConnectionsFactory:
        return self.__connections_factory

    @property
    def queues_repository(self) -> QueueRepositoryInterface:
        return self.__queues_repository

    @property
    def listeners_repository(self) -> ListenerRepositoryInterface:
        return self.__listeners_repository

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        pass

    def load_one(self, connection_id: str) -> Connection:
        pass

    def persist(self, channel_id: str, connection: Connection):
        pass

    def delete(self, connection_id: str):
        pass


class InMemoryQueueRepository(QueueRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def load(self, connection_id: str) -> InMemoryQueue:
        return self.storage.fetch_one(connection_id)

    def persist(self, connection_id: str, queue: InMemoryQueue):
        return self.storage.upsert(connection_id, queue)

    def delete(self, connection_id: str):
        self.storage.delete(connection_id)


class InMemoryListenerRepository(ListenerRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def load(self, connection_id: str) -> MessageQueueListener:
        return self.storage.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: MessageQueueListener):
        self.storage.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.storage.delete(connection_id)
