from typing import Callable, Generic, Iterable, cast

from eric_sse.connection import DefaultConnectionsFactory, L, Q
from eric_sse.entities import AbstractChannel
from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannelRepository
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import AbstractChannelRepository, ConnectionRepository, KvListenerRepository, \
    KvQueueRepository, KvStorage, PrefixedStorage


class Facade(Generic[L, Q]):
    """
    Single entry point for applications that persist everything using one storage engine.

    Channels, connections, listeners and queues share the given storage instance, each under its own key namespace.

    :param ~eric_sse.repository.KvStorage storage: The storage engine instance.
    :param listener_class: Class of listeners created by :meth:`add_listener`. Defaults to :class:`~eric_sse.listener.MessageQueueListener`.
    :param queue_factory: Called once per connection to create its queue. Defaults to :class:`~eric_sse.queues.InMemoryQueue`.
    :param repository_class: Channel repository to use. Defaults to :class:`~eric_sse.prefabs.SSEChannelRepository`.
    :param queue_repository_class: Queue repository to use. Defaults to :class:`~eric_sse.repository.KvQueueRepository`. Override it when queues need cleanup on deletion.
    """
    def __init__(
            self,
            storage: KvStorage,
            listener_class: type[L] = MessageQueueListener,
            queue_factory: Callable[[], Q] = InMemoryQueue,
            repository_class: type[AbstractChannelRepository] = SSEChannelRepository,
            queue_repository_class: type[KvQueueRepository] = KvQueueRepository
    ):
        self.__repository = repository_class(
            storage=PrefixedStorage(storage, 'channel:'),
            connections_repository=ConnectionRepository(
                storage=PrefixedStorage(storage, 'connection:'),
                listeners_repository=KvListenerRepository[L](PrefixedStorage(storage, 'listener:')),
                queues_repository=queue_repository_class(PrefixedStorage(storage, 'queue:'))
            ),
            connections_factory=DefaultConnectionsFactory(listener_class=listener_class, queue_factory=queue_factory)
        )

    @property
    def repository(self) -> AbstractChannelRepository:
        """The underlying channel repository, for advanced usages."""
        return self.__repository

    def create_channel(self, **channel_data) -> AbstractChannel:
        """Creates and persists a channel. **channel_data** are passed to the repository's create method."""
        channel = self.__repository.create(channel_data)
        self.__repository.persist(channel)
        return channel

    def get_channel(self, channel_id: str) -> AbstractChannel:
        return self.__repository.load_one(channel_id)

    def get_channels(self) -> Iterable[AbstractChannel]:
        return self.__repository.load_all()

    def delete_channel(self, channel_id: str):
        self.__repository.delete(channel_id)

    def add_listener(self, channel_id: str) -> L:
        """Creates a listener, subscribes it to given channel and persists it."""
        channel = self.__repository.load_one(channel_id)
        listener = channel.add_listener()
        self.__repository.persist(channel)
        return cast(L, listener)

    def remove_listener(self, channel_id: str, listener_id: str):
        channel = self.__repository.load_one(channel_id)
        channel.remove_listener(listener_id)
        self.__repository.persist(channel)
