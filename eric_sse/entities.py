import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException, InvalidChannelException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract, Message
from eric_sse.queue import Queue
from eric_sse.repository import AbstractMessageQueueRepository, InMemoryMessageQueueRepository

logger = eric_sse.get_logger()

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_eof'
MESSAGE_TYPE_INTERNAL_ERROR = '_eric_error'


class ConnectionManager:
    def __init__(self, queues_repository: AbstractMessageQueueRepository):
        self.__listeners: dict[str: MessageQueueListener] = {}
        self.__queues: dict[str: Queue] = {}
        self.__queues_factory = queues_repository


    def add_listener(self) -> MessageQueueListener:
        """Add the default listener"""
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, listener: MessageQueueListener):
        """
        Adds a listener to channel
        """
        self.__listeners[listener.id] = listener
        self.__queues[listener.id] = self.__queues_factory.create()

        self.__queues_factory.persist({listener.id: listener}, {listener.id: self.__queues[listener.id]})

    def remove_listener(self, listener_id: str):
        self.get_queue(listener_id=listener_id).delete()
        del self.__queues[listener_id]
        del self.__listeners[listener_id]
        self.__queues_factory.delete(listener_id)

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
        return self.__listeners

class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    :class:`eric_sse.queue.InMemoryMessageQueueFactory` is the default implementation used for queues_factory
    see :class:`eric_sse.prefabs.SSEChannel`

    :param int stream_delay_seconds: Wait time in seconds between message delivery.

    :param eric_sse.repository.AbstractMessageQueueRepository queues_repository:
    """
    def __init__(
            self,
            stream_delay_seconds: int = 0,
            queues_repository: AbstractMessageQueueRepository | None = None
    ):
        self.id: str = eric_sse.generate_uuid()
        self.stream_delay_seconds = stream_delay_seconds

        queues_repository = queues_repository if queues_repository else InMemoryMessageQueueRepository()
        self.__connection_manager: ConnectionManager = ConnectionManager(queues_repository)


    def add_listener(self) -> MessageQueueListener:
        """Add the default listener"""
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, listener: MessageQueueListener):
        return self.__connection_manager.register_listener(listener)

    def remove_listener(self, listener_id: str):
        self.__connection_manager.remove_listener(listener_id)

    def deliver_next(self, listener_id: str) -> MessageContract:
        """
        Returns next message for given listener id.

        Raises a NoMessagesException if queue is empty
        """
        listener = self.get_listener(listener_id)
        if listener.is_running_sync():
            msg = self._get_queue(listener_id).pop()
            listener.on_message(msg)
            return msg
        raise NoMessagesException

    def _get_queue(self, listener_id: str) -> Queue:
        return self.__connection_manager.get_queue(listener_id)

    def dispatch(self, listener_id: str, msg: MessageContract):
        """Adds a message to listener's queue"""

        self.__add_to_queue(listener_id, msg)
        logger.debug(f"Dispatched {msg} to {listener_id}")

    def __add_to_queue(self, listener_id: str, msg: MessageContract):
        self._get_queue(listener_id).push(msg)

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

        A message with type = 'error' is yeld on invalid listener or channel
        """

        def new_messages():
            try:
                yield self.deliver_next(listener.id)
            except NoMessagesException:
                ...

        async def event_generator() -> AsyncIterable[dict]:

            while True:
                # If client closes connection, stop sending events
                if not await listener.is_running():
                    logger.debug("Listener stopped. Exiting")
                    break

                try:
                    for message in new_messages():
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
        listener.start_sync()
        return self.message_stream(listener)

    def notify_end(self):
        """Broadcasts a MESSAGE_TYPE_CLOSED Message"""
        self.broadcast(Message(msg_type=MESSAGE_TYPE_CLOSED))
