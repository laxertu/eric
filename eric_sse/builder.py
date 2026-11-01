from typing import Callable

from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface
from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannelRepository
from eric_sse.queues import Queue, InMemoryQueue
from eric_sse.repository import AbstractChannelRepository, ConnectionRepository, InMemoryStorage, KvListenerRepository, \
    KvQueueRepository, KvStorage, PrefixedStorage


class ChannelRepositoryBuilder:
    """
    Wires a channel repository and its connections, listeners and queues repositories.

    Every part is stored in **storage** under its own namespace (``channel:``, ``connection:``, ``listener:``, ``queue:``),
    unless a dedicated storage or repository is given for it. Each method returns the builder, so calls can be chained::

        repository = (
            ChannelRepositoryBuilder(storage)
            .listeners(MyListener)
            .queues_repository(RedisQueuesRepository(redis_connection))
            .build()
        )

    Channels built by the resulting repository create their listeners and queues through it.
    Nothing is persisted implicitly: call the repository's ``persist`` when needed.

    When a part is configured more than once, the last call wins.

    :param ~eric_sse.repository.KvStorage storage: Default storage. Defaults to a new :class:`~eric_sse.repository.InMemoryStorage`.
    """
    def __init__(self, storage: KvStorage | None = None):
        self.__storage = storage if storage is not None else InMemoryStorage()
        self.__channels_repository_class: type[AbstractChannelRepository] = SSEChannelRepository
        self.__channels_storage: KvStorage | None = None
        self.__connections_storage: KvStorage | None = None
        self.__listener_class: type[MessageQueueListener] = MessageQueueListener
        self.__listeners_storage: KvStorage | None = None
        self.__listeners_repository: ListenerRepositoryInterface | None = None
        self.__queue_factory: Callable[[], Queue] = InMemoryQueue
        self.__queues_storage: KvStorage | None = None
        self.__queues_repository: QueueRepositoryInterface | None = None

    def channels(
            self,
            repository_class: type[AbstractChannelRepository] = SSEChannelRepository,
            storage: KvStorage | None = None
    ) -> 'ChannelRepositoryBuilder':
        """
        :param repository_class: Class of the channel repository to build. Defaults to :class:`~eric_sse.prefabs.SSEChannelRepository`.
        :param storage: Dedicated storage for channels.
        """
        self.__channels_repository_class = repository_class
        self.__channels_storage = storage
        return self

    def connections(self, storage: KvStorage) -> 'ChannelRepositoryBuilder':
        """
        :param storage: Dedicated storage for connections.
        """
        self.__connections_storage = storage
        return self

    def listeners(
            self,
            listener_class: type[MessageQueueListener] = MessageQueueListener,
            storage: KvStorage | None = None
    ) -> 'ChannelRepositoryBuilder':
        """
        Uses a :class:`~eric_sse.repository.KvListenerRepository`.

        :param listener_class: Class of listeners created by channels. Defaults to :class:`~eric_sse.listener.MessageQueueListener`.
        :param storage: Dedicated storage for listeners.
        """
        self.__listener_class = listener_class
        self.__listeners_storage = storage
        self.__listeners_repository = None
        return self

    def listeners_repository(self, repository: ListenerRepositoryInterface) -> 'ChannelRepositoryBuilder':
        """Uses a custom listeners repository, that also decides which listeners are created."""
        self.__listeners_repository = repository
        return self

    def queues(
            self,
            queue_factory: Callable[[], Queue] = InMemoryQueue,
            storage: KvStorage | None = None
    ) -> 'ChannelRepositoryBuilder':
        """
        Uses a :class:`~eric_sse.repository.KvQueueRepository`.

        :param queue_factory: Called once per connection to create its queue. Defaults to :class:`~eric_sse.queues.InMemoryQueue`.
        :param storage: Dedicated storage for queues.
        """
        self.__queue_factory = queue_factory
        self.__queues_storage = storage
        self.__queues_repository = None
        return self

    def queues_repository(self, repository: QueueRepositoryInterface) -> 'ChannelRepositoryBuilder':
        """Uses a custom queues repository, that also decides which queues are created."""
        self.__queues_repository = repository
        return self

    def __storage_for(self, namespace: str, storage: KvStorage | None) -> KvStorage:
        return PrefixedStorage(storage if storage is not None else self.__storage, f'{namespace}:')

    def build(self) -> AbstractChannelRepository:
        """Returns a new channel repository. The builder can be reused."""
        listeners_repository = self.__listeners_repository or KvListenerRepository(
            self.__storage_for('listener', self.__listeners_storage), listener_class=self.__listener_class
        )
        queues_repository = self.__queues_repository or KvQueueRepository(
            self.__storage_for('queue', self.__queues_storage), queue_factory=self.__queue_factory
        )
        return self.__channels_repository_class(
            storage=self.__storage_for('channel', self.__channels_storage),
            connections_repository=ConnectionRepository(
                storage=self.__storage_for('connection', self.__connections_storage),
                listeners_repository=listeners_repository,
                queues_repository=queues_repository
            )
        )
