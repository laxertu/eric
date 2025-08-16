from abc import ABC, abstractmethod
from collections.abc import AsyncIterable

from eric_sse.entities import AbstractChannel
from eric_sse.connection import Connection
from eric_sse.interfaces import (ChannelRepositoryInterface, ConnectionRepositoryInterface, ListenerRepositoryInterface,
                                 QueueRepositoryInterface)
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue
from eric_sse.inmemory import (InMemoryChannelRepository, InMemoryConnectionRepository, InMemoryListenerRepository,
                               InMemoryQueueRepository)
from eric_sse.exception import InvalidChannelException

class ApplicationTemplate(ABC):
    def __init__(
            self,
            channel_repository: ChannelRepositoryInterface = InMemoryChannelRepository(),
            connection_repository: ConnectionRepositoryInterface = InMemoryConnectionRepository(),
            listener_repository: ListenerRepositoryInterface = InMemoryListenerRepository(),
            queue_repository: QueueRepositoryInterface = InMemoryQueueRepository(),
    ):
        self._channel_repository = channel_repository
        self._connection_repository = connection_repository
        self._listener_repository = listener_repository
        self._queue_repository = queue_repository
        self._channels: set[str] = set()

    @abstractmethod
    def _create_channel(self) -> AbstractChannel:
        ...

    @abstractmethod
    def _create_listener(self) -> MessageQueueListener:
        ...

    @abstractmethod
    def _create_queue(self) -> Queue:
        ...

    def _create_connection(self) -> Connection:
        return Connection(listener=self._create_listener(), queue=self._create_queue())

    def boot(self) -> dict[str, AbstractChannel]:
        channels: dict[str, AbstractChannel] = {}
        for channel in self._channel_repository.load_all():
            for connection in self._connection_repository.load_all(channel_id=channel.id):
                connection.listener = self._listener_repository.load(connection_id=connection.id)
                connection.queue = self._queue_repository.load(connection_id=connection.id)
                channel.register_connection(connection)
            channels[channel.id] = channel
        return channels

    def create_channel(self) -> AbstractChannel:
        channel = self._create_channel()
        self._channel_repository.persist(channel)
        self._channels.add(channel.id)
        return channel

    def load_channel(self, channel_id: str) -> AbstractChannel:
        channel = self._channel_repository.load_one(channel_id=channel_id)
        self._channels.add(channel.id)
        return channel

    def save_channel(self, channel: AbstractChannel):
        self._channel_repository.persist(channel)
        for connection in channel.get_connections():
            self._save_connection(connection)

    def _save_connection(self, connection: Connection):
        self._connection_repository.persist(connection)
        self._listener_repository.persist(connection.id, connection.listener)
        self._queue_repository.persist(connection.id, connection.queue)

    def delete_channel(self, channel_id: str):
        self._channel_repository.delete(channel_id)
        for connection in self._connection_repository.load_all(channel_id):
            self.unsubscribe_channel(channel_id=channel_id, connection_id=connection.id)
        self._channels.remove(channel_id)

    def subscribe_channel(self, channel: AbstractChannel):
        if channel.id not in self._channels:
            raise InvalidChannelException(f'Unknown channel {channel.id}')

        connection = self._create_connection()
        channel.register_connection(connection)
        self._save_connection(connection)
        return connection

    def unsubscribe_channel(self, channel_id: str, connection_id: str):
        channel = self._channel_repository.load_one(channel_id=channel_id)
        connection = self._connection_repository.load_one(connection_id=connection_id)
        channel.remove_listener(connection.listener.id)
        self._delete_connection(connection_id)

    def _delete_connection(self, connection_id: str):
        self._listener_repository.delete(connection_id=connection_id)
        self._queue_repository.delete(connection_id=connection_id)
        self._connection_repository.delete(connection_id)

    async def listen_to_channel(self, channel: AbstractChannel) -> AsyncIterable[any]:
        connection = self.subscribe_channel(channel)
        return channel.message_stream(connection.listener)
