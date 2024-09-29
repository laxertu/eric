from typing import Any, Callable

from eric_sse import get_logger
from eric_sse.entities import AbstractChannel, Message, MessageQueueListener, MESSAGE_TYPE_CLOSED
from concurrent.futures import ThreadPoolExecutor

logger = get_logger()

class SSEChannel(AbstractChannel):

    """
    SSE streaming channel.

    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
    Currently, 'id' field is not supported.
    """
    def __init__(self, retry_timeout_milliseconds: int = 5):
        super().__init__()
        self.retry_timeout_milliseconds = retry_timeout_milliseconds

    def adapt(self, msg: Message) -> Any:
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }


class ThreadPoolListener(MessageQueueListener):
    def __init__(self, callback: Callable[[Message], None], executor: ThreadPoolExecutor):
        super().__init__()
        self.__callback = callback
        self.executor = executor


    def on_message(self, msg: Message) -> None:
        if msg.type == MESSAGE_TYPE_CLOSED:
            logger.info(f"Stopping listener {self.id}")
            self.stop_sync()
        else:
            with self.executor:
                self.__callback(msg)



class DataProcessingChannel(AbstractChannel):
    """
    Channel intended for concurrent processing of data.

    Relies on concurrent.futures.ThreadPoolExecutor.

    MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

    Note that:

     * same callback is invoked, no matter of message type
     * callback execution order is not guaranteed (to be the same as the one while dispatching to channel)
    """

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0):
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)

    def notify_end(self):
        """Broadcasts a MESSAGE_TYPE_CLOSED Message"""
        self.broadcast(Message(type=MESSAGE_TYPE_CLOSED))

    def add_threaded_listener(self, callback: Callable[[Message], None]) -> ThreadPoolListener:
        """Adds a threaded listener"""
        l = ThreadPoolListener(callback, self.__executor)
        self.register_listener(l)
        return l

    def adapt(self, msg: Message) -> Any:
        return {f'processed message {msg.payload}'}


