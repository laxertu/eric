from typing import Iterable

from eric_sse.persistence import KvStorageEngine, ItemNotFound
from eric_sse.serializable import ChannelRepository, ConnectionRepository, QueueRepository
from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.queues import Queue

class InMemoryStorage(KvStorageEngine):

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
            raise ItemNotFound(key)

    def delete(self, key: str):
        del InMemoryStorage.objects[key]

class InMemoryConnectionRepository(ConnectionRepository):
    def __init__(self, connections: dict[str, Connection] = None):
        super().__init__(storage_engine=InMemoryStorage(objects=connections or {}))

class InMemoryChannelRepository(ChannelRepository):
    def __init__(self, channels: dict[str, AbstractChannel] = None):
        super().__init__(storage_engine=InMemoryStorage(objects=channels or {}))

class InMemoryQueueRepository(QueueRepository):
    def __init__(self, queues: dict[str, Queue] = None):
        super().__init__(storage_engine=InMemoryStorage(objects=queues or {}))
