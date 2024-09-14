import asyncio
import json
from threading import Lock

from abc import ABC, abstractmethod
from dataclasses import dataclass

import eric
logger = eric.get_logger()

class InvalidChannelException(Exception):
    ...

class InvalidListenerException(Exception):
    ...

class NoMessagesException(Exception):
    ...

class InvalidMessageFormat(Exception):
    ...


@dataclass
class Message:
    type: str
    payload: dict | list | str | None = None

def create_from_json(raw_txt: str) -> Message:
    try:
        parsed = json.loads(raw_txt)
        return Message(
            type=parsed['type'],
            payload=parsed['payload']
        )
    except json.JSONDecodeError as e:
        raise InvalidMessageFormat(e)
    except KeyError as e:
        raise InvalidMessageFormat(e)

def create_simple_mesage(txt: str) -> Message:
    return Message(type='txt', payload=txt)

class MessageQueueListener(ABC):
    NEXT_ID = 1

    def __init__(self):
        with Lock():
            self.id: str = str(MessageQueueListener.NEXT_ID)
            MessageQueueListener.NEXT_ID += 1
        self.__is_running: bool = False

    async def start(self) -> None:
        self.__is_running = True
        await self.on_start()

    async def on_start(self) -> None:
        pass

    async def is_running(self) -> bool:
        return self.__is_running

    async def stop(self) -> None:
        self.__is_running = False

    def on_message(self, msg: Message) -> None:
        ...

class AbstractChannel(ABC):
    NEXT_ID = 1

    def __init__(self):
        logger.info(f'Creating channel {SSEChannel.NEXT_ID}')
        with Lock():
            self.id: str = str(SSEChannel.NEXT_ID)
            SSEChannel.NEXT_ID += 1

        self.listeners: dict[str: MessageQueueListener] = {}
        self.queues: dict[str: list[Message]] = {}


    def add_listener(self, l_class: MessageQueueListener.__class__) -> MessageQueueListener:
        l = l_class()
        self.register_listener(l)
        return l

    def register_listener(self, l: MessageQueueListener):
        self.listeners[l.id] = l
        self.queues[l.id] = []

    def remove_listener(self, l_id: str):
        del self.queues[l_id]
        del self.listeners[l_id]

    def deliver_next(self, listener_id: str) -> Message:
        try:
            msg = self.__get_queue(listener_id).pop(0)
            self.get_listener(listener_id).on_message(msg)

            return msg
        except IndexError:
            raise NoMessagesException

    def __get_queue(self, listener_id: str) -> list[Message]:
        try:
            return self.queues[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}")


    def dispatch(self, listener: MessageQueueListener, msg: Message):
        try:
            self._add_to_queue(listener.id, msg)
        except InvalidListenerException:
            self.register_listener(listener)
        logger.debug(f"Pending {len(self.queues[listener.id])} messages")

    def _add_to_queue(self, listener_id: str, msg: Message):
        self.__get_queue(listener_id).append(msg)

    def broadcast(self, msg: Message):
        for listener_id in self.listeners.keys():
            self.dispatch(listener=self.get_listener(listener_id), msg=msg)


    def get_listener(self, listener_id: str) -> MessageQueueListener:
        try:
            return self.listeners[listener_id]
        except KeyError:
            raise InvalidListenerException

    @abstractmethod
    async def message_stream(self, listener: MessageQueueListener):
        ...


class SSEChannel(AbstractChannel):

    def __init__(self):
        super().__init__()
        self.stream_delay_seconds = 1
        self.retry_timeout_millisedonds = 15000

    async def message_stream(self, listener: MessageQueueListener):

        def new_messages():
            try:
                yield self.deliver_next(listener.id)
            except NoMessagesException:
                ...

        async def event_generator():
            while True:
                # If client closes connection, stop sending events
                if not await listener.is_running():
                    break

                try:
                    for message in new_messages():
                        yield {
                            "event": message.type,
                            "retry": self.retry_timeout_millisedonds,
                            "data": message.payload
                        }

                    await asyncio.sleep(self.stream_delay_seconds)
                except InvalidChannelException as e:
                    logger.debug(e)
                    await listener.stop()
                    yield {
                        "event": "_eric_channel_closed",
                        "data": None
                    }

        return event_generator()
