import asyncio
from threading import Lock

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterable, Any

import eric_sse
from eric_sse.exception import InvalidChannelException, InvalidListenerException, NoMessagesException

logger = eric_sse.get_logger()

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_closed'

@dataclass
class Message:
    """
    Models a message

    It's just a container of information identified by a type.
    For validation purposes you can override MessageQueueListener.on_message
    """
    type: str
    payload: dict | list | str | int | float | None = None


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

    def on_message(self, msg: Message) -> None:
        """Event handler. It executes when a message is delivered to client"""
        pass


class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management. SSEChannel is the default implementation
    """
    NEXT_ID = 1

    def __init__(self, stream_delay_seconds: int = 0):
        logger.info(f'Creating channel {AbstractChannel.NEXT_ID}')
        with Lock():
            self.id: str = str(AbstractChannel.NEXT_ID)
            AbstractChannel.NEXT_ID += 1

        self.listeners: dict[str: MessageQueueListener] = {}
        self.queues: dict[str: list[Message]] = {}
        self.stream_delay_seconds = stream_delay_seconds
        self.__streaming_listeners: set[str] = set()


    def add_listener(self) -> MessageQueueListener:
        """Add the default listener"""
        l = MessageQueueListener()
        self.register_listener(l)
        return l

    def register_listener(self, l: MessageQueueListener):
        """
        Adds a listener to channel
        """
        self.listeners[l.id] = l
        self.queues[l.id] = []

    def remove_listener(self, l_id: str):
        del self.queues[l_id]
        del self.listeners[l_id]

    def deliver_next(self, listener_id: str) -> Message:
        """
        Returns next message for given listener id.

        Raises a NoMessagesException if queue is empty
        """
        if self.get_listener(listener_id).is_running_sync():
            try:
                with Lock():
                    msg = self.__get_queue(listener_id).pop(0)
                    self.get_listener(listener_id).on_message(msg)

                    return msg
            except IndexError:
                raise NoMessagesException
        raise NoMessagesException

    def __get_queue(self, listener_id: str) -> list[Message]:
        try:
            return self.queues[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}")

    def dispatch(self, listener_id: str, msg: Message):
        """Adds a message to listener's queue"""

        self.__add_to_queue(listener_id, msg)
        logger.debug(f"Pending {len(self.queues[listener_id])} messages")

    def __add_to_queue(self, listener_id: str, msg: Message):
        self.__get_queue(listener_id).append(msg)

    def broadcast(self, msg: Message):
        """Enqueue a message to all listeners"""
        for listener_id in self.listeners.keys():
            self.dispatch(listener_id, msg=msg)

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        try:
            return self.listeners[listener_id]
        except KeyError:
            raise InvalidListenerException

    @abstractmethod
    def adapt(self, msg: Message) -> Any:
        ...

    async def message_stream(self, listener: MessageQueueListener) -> AsyncIterable[dict]:
        """
        Entry point for message streaming

        In case of failure at channel resolution time, a special message with type=MESSAGE_TYPE_CLOSED is sent, and
        correspondant listener is stopped
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
                    break

                try:
                    for message in new_messages():
                        yield self.adapt(message)

                    await asyncio.sleep(self.stream_delay_seconds)
                except InvalidChannelException as e:
                    logger.info(f"Stopping listener {listener.id}")
                    logger.debug(e)
                    await listener.stop()
                    yield self.adapt(Message(type=MESSAGE_TYPE_CLOSED))

        return event_generator()


    def notify_end(self):
        """Broadcasts a MESSAGE_TYPE_CLOSED Message"""
        self.broadcast(Message(type=MESSAGE_TYPE_CLOSED))

