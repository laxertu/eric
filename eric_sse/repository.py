from typing import Iterable

from eric_sse.connection import Connection, ConnectionsFactory
from eric_sse.entities import ChannelRepositoryInterface, AbstractChannel
from eric_sse.exception import ItemNotFound
from eric_sse.interfaces import ConnectionRepositoryInterface, ListenerRepositoryInterface, \
    QueueRepositoryInterface, KvStorageInterface


class ConnectionRepository(ConnectionRepositoryInterface):
    """
    Concrete Connection Repository

    Relies on :class:`~eric_sse.repository.KvStorage` abstraction for final writes of connections data, and on
    corresponding repositories for related objects ones.
    """
    def __init__(
            self,
            storage: KvStorageInterface,
            listeners_repository: ListenerRepositoryInterface,
            queues_repository: QueueRepositoryInterface,
            connections_factory:ConnectionsFactory
    ):
        self.__storage = storage
        self.__listeners_repository = listeners_repository
        self.__queues_repository = queues_repository
        self.__connections_factory = connections_factory

    CONNECTIONS_BY_CHANNEL_PREFIX: str = 'ch_cn'
    CONNECTIONS_PREFIX: str = 'cn_ch'

    @property
    def queues_repository(self) -> QueueRepositoryInterface:
        return self.__queues_repository

    @property
    def listeners_repository(self) -> ListenerRepositoryInterface:
        return self.__listeners_repository

    @property
    def connections_factory(self) -> ConnectionsFactory:
        return self.__connections_factory

    def _load_connection(self, connection_id: str) -> Connection:
        try:
            _ = self.__storage.fetch_one(f'{self.CONNECTIONS_PREFIX}:{connection_id}')
        except ItemNotFound as e:
            raise e from None

        listener = self.__listeners_repository.load(connection_id=connection_id)
        queue = self.__queues_repository.load(connection_id=connection_id)

        return Connection(listener=listener, queue=queue, connection_id=connection_id)

    def load_all(self, channel_id: str) -> Iterable[Connection]:
        for connection_data in self.__storage.fetch_by_prefix(f'{self.CONNECTIONS_BY_CHANNEL_PREFIX}:{channel_id}:'):
            yield self._load_connection(connection_id=connection_data['cn_id'])


    def load_one(self, connection_id: str) -> Connection:
        return self._load_connection(connection_id=connection_id)

    def persist(self, channel_id: str, connection: Connection):

        self.__listeners_repository.persist(connection_id=connection.id, listener=connection.listener)
        self.__queues_repository.persist(connection_id=connection.id, queue=connection.queue)
        self.__storage.upsert(key=f'{self.CONNECTIONS_PREFIX}:{connection.id}', value={'ch_id': channel_id, 'cn_id': connection.id})
        self.__storage.upsert(key=f'{self.CONNECTIONS_BY_CHANNEL_PREFIX}:{channel_id}:{connection.id}', value={'ch_id': channel_id, 'cn_id': connection.id})


    def delete(self, connection_id: str):
        try:
            connection_data = self.__storage.fetch_one(key=f'{self.CONNECTIONS_PREFIX}:{connection_id}')
        except ItemNotFound:
            return

        channel_id = connection_data['ch_id']

        self.__listeners_repository.delete(connection_id=connection_id)
        self.__queues_repository.delete(connection_id=connection_id)
        self.__storage.delete(key=f'{self.CONNECTIONS_PREFIX}:{connection_id}')
        self.__storage.delete(key=f'{self.CONNECTIONS_BY_CHANNEL_PREFIX}:{channel_id}:{connection_id}')


class ChannelRepository(ChannelRepositoryInterface):
    def __init__(
            self,
            storage: KvStorageInterface,
            connections_repository: ConnectionRepositoryInterface
    ):
        self.__storage = storage
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

    def create(self, channel_data: dict) -> AbstractChannel:
        pass