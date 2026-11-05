from typing import Callable, Generic

from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.interfaces import C, ListenerRepositoryInterface, QueueRepositoryInterface
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue, InMemoryQueue
from eric_sse.repository import ChannelRepository, ConnectionRepository, InMemoryStorage, KvListenerRepository, \
    KvQueueRepository, KvStorage, PrefixedStorage


class ChannelRepositoryBuilder(Generic[C]):
    """
    Wires a channel repository and its connections, listeners and queues repositories.

    Every part is stored in **storage** under its own namespace (``channel:``, ``connection:``, ``listener:``, ``queue:``),
    unless a dedicated storage or repository is given for it. Each method returns the builder, so calls can be chained::

        repository = (
            ChannelRepositoryBuilder(SSEChannel, storage)
            .listeners(MyListener)
            .queues_repository(MyQueuesRepository(connection))
            .build()
        )

    Channels built by the resulting repository create their listeners and queues through it.
    Nothing is persisted implicitly: call the repository's ``persist`` when needed.

    When a part is configured more than once, the last call wins, except for error handlers, that are added.

    The builder is generic in **channel_class**, so type checkers know which channels the repository returns.

    :param channel_class: Class of channels the repository creates, loads and persists, e.g. :class:`~eric_sse.prefabs.SSEChannel`.
    :param ~eric_sse.repository.KvStorage storage: Default storage. Defaults to a new :class:`~eric_sse.repository.InMemoryStorage`.
    """
    def __init__(self, channel_class: type[C], storage: KvStorage | None = None):
        self.__storage = storage if storage is not None else InMemoryStorage()
        self.__channel_class = channel_class
        self.__channels_storage: KvStorage | None = None
        self.__connections_storage: KvStorage | None = None
        self.__listener_factory: Callable[[], MessageQueueListener] = MessageQueueListener
        self.__listeners_storage: KvStorage | None = None
        self.__listeners_repository: ListenerRepositoryInterface | None = None
        self.__queue_factory: Callable[[], Queue] = InMemoryQueue
        self.__queues_storage: KvStorage | None = None
        self.__queues_repository: QueueRepositoryInterface | None = None
        self.__queuing_error_handlers: list[QueuingErrorHandler] = []
        self.__listener_error_handlers: list[ListenerErrorHandler] = []

    def channels(self, storage: KvStorage) -> 'ChannelRepositoryBuilder[C]':
        """
        :param storage: Dedicated storage for channels.
        """
        self.__channels_storage = storage
        return self

    def connections(self, storage: KvStorage) -> 'ChannelRepositoryBuilder[C]':
        """
        :param storage: Dedicated storage for connections.
        """
        self.__connections_storage = storage
        return self

    def listeners(
            self,
            listener_factory: Callable[[], MessageQueueListener] = MessageQueueListener,
            storage: KvStorage | None = None
    ) -> 'ChannelRepositoryBuilder[C]':
        """
        Uses a :class:`~eric_sse.repository.KvListenerRepository`.

        :param listener_factory: Called once per connection to create its listener: a listener class, or any callable
            returning a listener, e.g. ``lambda: ProfiledListener(MyListener())``.
            Defaults to :class:`~eric_sse.listener.MessageQueueListener`.
        :param storage: Dedicated storage for listeners.
        """
        self.__listener_factory = listener_factory
        self.__listeners_storage = storage
        self.__listeners_repository = None
        return self

    def listeners_repository(self, repository: ListenerRepositoryInterface) -> 'ChannelRepositoryBuilder[C]':
        """Uses a custom listeners repository, that also decides which listeners are created."""
        self.__listeners_repository = repository
        return self

    def queues(
            self,
            queue_factory: Callable[[], Queue] = InMemoryQueue,
            storage: KvStorage | None = None
    ) -> 'ChannelRepositoryBuilder[C]':
        """
        Uses a :class:`~eric_sse.repository.KvQueueRepository`.

        :param queue_factory: Called once per connection to create its queue. Defaults to :class:`~eric_sse.queues.InMemoryQueue`.
        :param storage: Dedicated storage for queues.
        """
        self.__queue_factory = queue_factory
        self.__queues_storage = storage
        self.__queues_repository = None
        return self

    def queues_repository(self, repository: QueueRepositoryInterface) -> 'ChannelRepositoryBuilder[C]':
        """Uses a custom queues repository, that also decides which queues are created."""
        self.__queues_repository = repository
        return self

    def queuing_error_handler(self, handler: QueuingErrorHandler) -> 'ChannelRepositoryBuilder[C]':
        """
        Adds a handler registered on every channel created or loaded by the repository.
        Unlike other parts, repeated calls add handlers instead of replacing them.
        """
        self.__queuing_error_handlers.append(handler)
        return self

    def listener_error_handler(self, handler: ListenerErrorHandler) -> 'ChannelRepositoryBuilder[C]':
        """
        Adds a handler registered on every channel created or loaded by the repository.
        Unlike other parts, repeated calls add handlers instead of replacing them.
        """
        self.__listener_error_handlers.append(handler)
        return self

    def __storage_for(self, namespace: str, storage: KvStorage | None) -> KvStorage:
        return PrefixedStorage(storage if storage is not None else self.__storage, f'{namespace}:')

    def build(self) -> ChannelRepository[C]:
        """Returns a new channel repository. The builder can be reused."""
        listeners_repository = self.__listeners_repository or KvListenerRepository(
            self.__storage_for('listener', self.__listeners_storage), listener_factory=self.__listener_factory
        )
        queues_repository = self.__queues_repository or KvQueueRepository(
            self.__storage_for('queue', self.__queues_storage), queue_factory=self.__queue_factory
        )
        return ChannelRepository(
            storage=self.__storage_for('channel', self.__channels_storage),
            channel_class=self.__channel_class,
            connections_repository=ConnectionRepository(
                storage=self.__storage_for('connection', self.__connections_storage),
                listeners_repository=listeners_repository,
                queues_repository=queues_repository
            ),
            queuing_error_handlers=self.__queuing_error_handlers,
            listener_error_handlers=self.__listener_error_handlers
        )
