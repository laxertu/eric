from typing import Any, Callable

from asyncio import Future

from eric_sse import get_logger
from eric_sse.entities import AbstractChannel, Message, MessageQueueListener, MESSAGE_TYPE_CLOSED

logger = get_logger()

class SSEChannel(AbstractChannel):
    """
    SSE streaming channel.

    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
    Currently, 'id' field is not supported.
    """
    def adapt(self, msg: Message) -> Any:
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }


class ThreadPoolListener(MessageQueueListener):
    """
    CURRENTLY NOT SUITABLE FOR PRODUCTION ENVIRONMENTS.

    Listener intended for concurrent processing of data.

    Relies on concurrent.futures.ThreadPoolExecutor.

    MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

    Note that:

     * same callback is invoked, no matter of message type
     * callback execution order is not guaranteed (to be the same as the one while dispatching to channel)
    """
    def __init__(self, callback: Callable[[Message], None], max_workers: int):
        from concurrent.futures import ThreadPoolExecutor
        super().__init__()
        self.__callback = callback
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        self.__exec_after = max_workers
        self.__futures: list[Future] = []

    def on_message(self, msg: Message) -> None:
        if msg.type == MESSAGE_TYPE_CLOSED:
            for f in self.__futures:
                _ = f.result()
            logger.info(f"Stopping listener {self.id}")
            self.stop_sync()
        else:
            # TODO reset
            self.__futures.append(self.executor.submit(self.__callback, msg))
            if len(self.__futures) >= self.__exec_after:
                for f in self.__futures:
                    _ = f.result()



class DataProcessingChannel(SSEChannel):
    """Channel that invokes a callable in a Pool of threads"""

    def notify_end(self):
        self.broadcast(Message(type=MESSAGE_TYPE_CLOSED))

    def add_threaded_listener(self, callback: Callable[[Message], None], max_workers: int) -> ThreadPoolListener:
        """Adds a threaded listener"""
        l = ThreadPoolListener(callback, max_workers)
        self.register_listener(l)
        return l
