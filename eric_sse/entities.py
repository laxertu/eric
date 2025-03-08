import asyncio
import traceback
from abc import ABC, abstractmethod
from threading import Lock
from typing import AsyncIterable, Any

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException
from eric_sse.message import MessageContract, Message
from eric_sse.queue import Queue, AbstractMessageQueueFactory, InMemoryMessageQueueFactory

logger = eric_sse.get_logger()

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_eof'
MESSAGE_TYPE_INTERNAL_ERROR = '_eric_error'


class MessageQueueListener(ABC):
    """
    Base class for listeners.

    Optionally you can override on_message method if you need to inject code at message delivery time.
    """
    NEXT_ID = 1

    def __init__(self):
        with Lock():
            self.id: str = str(MessageQueueListener.NEXT_ID)
            MessageQueueListener.NEXT_ID += 1
        self.__is_running: bool = False

    async def start(self) -> None:
        self.__is_running = True

    def start_sync(self) -> None:
        self.__is_running = True

    async def is_running(self) -> bool:
        return self.__is_running

    def is_running_sync(self) -> bool:
        return self.__is_running

    async def stop(self) -> None:
        self.__is_running = False

    def stop_sync(self) -> None:
        self.__is_running = False

    def on_message(self, msg: MessageContract) -> None:
        """Event handler. It executes when a message is delivered to client"""
        pass


class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    :class:`eric_sse.queue.InMemoryMessageQueueFactory` is the default implementation used for queues_factory
    see :class:`eric_sse.prefabs.SSEChannel`

    :param int stream_delay_seconds: Wait time in seconds between message delivery.

    :param eric_sse.queue.AbstractMessageQueueFactory queues_factory:
    """
    NEXT_ID = 1

    def __init__(
            self,
            stream_delay_seconds: int = 0,
            queues_factory: AbstractMessageQueueFactory | None = None
    ):
        logger.debug(f'Creating channel {AbstractChannel.NEXT_ID}')
        with Lock():
            self.id: str = str(AbstractChannel.NEXT_ID)
            AbstractChannel.NEXT_ID += 1

        self.stream_delay_seconds = stream_delay_seconds

        self.__listeners: dict[str: MessageQueueListener] = {}
        self.__queues: dict[str: Queue] = {}
        self.__queues_factory = queues_factory if queues_factory else InMemoryMessageQueueFactory()

    def _set_queues_factory(self, queues_factory: AbstractMessageQueueFactory):
        self.__queues_factory = queues_factory

    def add_listener(self) -> MessageQueueListener:
        """Add the default listener"""
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, l: MessageQueueListener):
        """
        Adds a listener to channel
        """
        self.__listeners[l.id] = l
        self.__queues[l.id] = self.__queues_factory.create()

    def remove_listener(self, l_id: str):
        self._get_queue(listener_id=l_id).delete()
        del self.__queues[l_id]
        del self.__listeners[l_id]

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
        try:
            return self.__queues[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}")

    def _set_queue(self, listener_id: str, queue: Queue):
        self.__queues[listener_id] = queue

    def dispatch(self, listener_id: str, msg: MessageContract):
        """Adds a message to listener's queue"""

        self.__add_to_queue(listener_id, msg)
        logger.debug(f"Dispatched {msg} to {listener_id}")

    def __add_to_queue(self, listener_id: str, msg: MessageContract):
        self._get_queue(listener_id).push(msg)

    def broadcast(self, msg: MessageContract):
        """Enqueue a message to all listeners"""
        for listener_id in self.__listeners.keys():
            self.dispatch(listener_id, msg=msg)

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        try:
            return self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException

    @abstractmethod
    def adapt(self, msg: MessageContract) -> Any:
        ...

    async def message_stream(self, listener: MessageQueueListener) -> AsyncIterable[Any]:
        """
        Entry point for message streaming
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

                except Exception as e:
                    logger.debug(traceback.format_exc())
                    logger.error(e)

        return event_generator()

    async def watch(self) -> AsyncIterable[Any]:
        listener = self.add_listener()
        listener.start_sync()
        return await self.message_stream(listener)

    def notify_end(self):
        """Broadcasts a MESSAGE_TYPE_CLOSED Message"""
        self.broadcast(Message(msg_type=MESSAGE_TYPE_CLOSED))
