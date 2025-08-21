from typing import Iterable

from eric_sse.interfaces import ConnectionRepositoryInterface, ChannelRepositoryInterface
from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
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
            # mal
        connections: InMemoryStorage = InMemoryStorage(),
    ):
        self.connections = connections or {}

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for connection in self.connections.fetch_all():
            yield connection

    def load_one(self, connection_id: str) -> Connection:
        return self.connections.get(connection_id)

    def persist(self, connection: Connection):
        self.connections.upsert(connection.id, connection)

    def delete(self, connection_id: str):
        self.connections.delete(connection_id)


class InMemoryChannelRepository(ChannelRepositoryInterface):
    def __init__(
            self,
            channels: dict[str, AbstractChannel] = None
    ):
        self.__channels = channels or {}

    def load_all(self) -> Iterable[AbstractChannel]:
        for channel in self.__channels.values():
            yield channel

    def load_one(self, channel_id: str) -> AbstractChannel:
        try:
            return self.__channels[channel_id]
        except KeyError:
            raise RepositoryError(f'Item not found {channel_id}') from None

    def persist(self, channel: AbstractChannel):
        self.__channels[channel.id] = channel

    def delete(self, channel_id: str):
        del self.__channels[channel_id]



