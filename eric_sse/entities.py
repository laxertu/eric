import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException, InvalidChannelException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract, Message
from eric_sse.queues import Queue
from eric_sse.persistence import ConnectionRepositoryInterface, InMemoryConnectionRepository
from eric_sse.connection import Connection

logger = eric_sse.get_logger()

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_eof'
MESSAGE_TYPE_INTERNAL_ERROR = '_eric_error'


class _ConnectionManager:
    """Maintains relationships between listeners and queues"""
    def __init__(self, channel_id: str, queues_repository: ConnectionRepositoryInterface):
        self.__channel_id = channel_id
        self.__listeners: dict[str: MessageQueueListener] = {}
        self.__queues: dict[str: Queue] = {}
        self.__queues_repository = queues_repository


    def load(self):
        for c in self.__queues_repository.load_all():
            self.__listeners[c.listener.id] = c.listener
            self.__queues[c.listener.id] = c.queue

    def add_listener(self) -> MessageQueueListener:
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, listener: MessageQueueListener):
        self.__listeners[listener.id] = listener
        self.__queues[listener.id] = self.__queues_repository.create_queue(listener_id=listener.id)
        self.__queues_repository.persist(
            channel_id=self.__channel_id,
            connection=Connection(listener=listener, queue=self.__queues[listener.id])
        )

    def register_connection(self, listener: MessageQueueListener, queue: Queue):
        self.__listeners[listener.id] = listener
        self.__queues[listener.id] = queue


    def remove_listener(self, listener_id: str):
        del self.__queues[listener_id]
        del self.__listeners[listener_id]

        self.__queues_repository.delete(channel_id=self.__channel_id, listener_id=listener_id)

    def get_queue(self, listener_id: str) -> Queue:
        try:
            return self.__queues[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}") from None

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        try:
            return self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException

    def get_listeners(self) -> dict[str, MessageQueueListener]:
        """Returns a dict mapping listener ids to listeners"""
        return self.__listeners

class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    :class:`eric_sse.queue.InMemoryMessageQueueFactory` is the default implementation used for queues_factory
    see :class:`eric_sse.prefabs.SSEChannel`

    :param int stream_delay_seconds: Wait time in seconds between message delivery.

    :param eric_sse.persistence.ConnectionRepositoryInterface connections_repository:
    """
    def __init__(
            self,
            channel_id: str | None = None,
            stream_delay_seconds: int = 0,
            connections_repository: ConnectionRepositoryInterface | None = None
    ):
        self.__id: str = eric_sse.generate_uuid() if channel_id is None else channel_id
        self.stream_delay_seconds = stream_delay_seconds

        connections_repository = connections_repository if connections_repository else InMemoryConnectionRepository()
        self.__connection_manager: _ConnectionManager = _ConnectionManager(channel_id, connections_repository)

    @property
    def id(self) -> str:
        return self.__id

    def get_listeners_ids(self) -> list[str]:
        return [l.id for l in self.__connection_manager.get_listeners().values()]

    def open(self):
        self.__connection_manager.load()


    def add_listener(self) -> MessageQueueListener:
        """Add the default listener"""
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, listener: MessageQueueListener):
        """Registers listener and creates corresponding queue"""
        return self.__connection_manager.register_listener(listener)

    def register_connection(self, listener: MessageQueueListener, queue: Queue):
        """Registers a Connection with listener and queue"""
        return self.__connection_manager.register_connection(listener, queue)

    def remove_listener(self, listener_id: str):
        self.__connection_manager.remove_listener(listener_id)

    def deliver_next(self, listener_id: str) -> MessageContract:
        """
        Returns next message for given listener id.

        Raises a NoMessagesException if queue is empty
        """
        listener = self.get_listener(listener_id)
        if listener.is_running():
            queue = self.__connection_manager.get_queue(listener.id)
            msg = queue.pop()
            listener.on_message(msg)
            return msg

        raise NoMessagesException

    def _get_queue(self, listener_id: str) -> Queue:
        return self.__connection_manager.get_queue(listener_id)

    def dispatch(self, listener_id: str, msg: MessageContract):
        """Adds a message to listener's queue"""

        queue = self._get_queue(listener_id)
        queue.push(msg)
        logger.debug(f"Dispatched {msg} to {listener_id}")

    def broadcast(self, msg: MessageContract):
        """Enqueue a message to all listeners"""
        for listener_id in self.__connection_manager.get_listeners():
            self.dispatch(listener_id, msg=msg)

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        return self.__connection_manager.get_listener(listener_id)

    @abstractmethod
    def adapt(self, msg: MessageContract) -> Any:
        ...

    async def message_stream(self, listener: MessageQueueListener) -> AsyncIterable[Any]:
        """
        Entry point for message streaming

        A message with type = 'error' is yield on invalid listener or channel
        """

        async def new_messages():
            try:
                result = self.deliver_next(listener.id)
                yield result
            except NoMessagesException:
                ...

        async def event_generator() -> AsyncIterable[dict]:

            while True:
                # If client closes connection, stop sending events
                if not listener.is_running():
                    logger.debug("Listener stopped. Exiting")
                    break

                try:
                    async for message in new_messages():
                        yield self.adapt(message)

                    await asyncio.sleep(self.stream_delay_seconds)
                except (InvalidListenerException, InvalidChannelException) as e:
                    yield self.adapt(Message(msg_type='error', msg_payload=e))
                except Exception as e:
                    logger.debug(traceback.format_exc())
                    logger.error(e)
                    yield self.adapt(Message(msg_type='error'))

        async for event in event_generator():
            yield event

    async def watch(self) -> AsyncIterable[Any]:
        # TODO tests
        listener = self.add_listener()
        listener.start()
        return self.message_stream(listener)
