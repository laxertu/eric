from typing import Any, Callable

from eric_sse.entities import AbstractChannel, Message, MessageQueueListener


class SSEChannel(AbstractChannel):
    """
    SSE streaming channel.

    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
    Currently, 'id' field is not supported.
    """
    def adapt(self, msg: Message) -> Any:
        return {
            "event": msg.type,
            "retry": self.retry_timeout_millisedonds,
            "data": msg.payload
        }


class ThreadPoolListener(MessageQueueListener):
    """
    Listener intended for consurrent processing of data.

    Relies on concurrent.futures.ThreadPoolExecutor.
    '_eric_channel_closed' Message type is intended as end of stream. Is shouls be considered as a reserved Message type
    """
    def __init__(self, callback: Callable, max_workers: int):
        from concurrent.futures import ThreadPoolExecutor
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.__callback = callback

    def on_message(self, msg: Message) -> None:
        if msg.type == '_eric_channel_closed':
            self.stop_sync()
        else:
            self.executor.submit(self.__callback, msg.payload)


class DataProcessingChannel(SSEChannel):

    def notify_end(self):
        self.broadcast(Message(type='_eric_channel_closed'))

    def add_threaded_listener(self, callback: Callable, max_workers: int) -> ThreadPoolListener:

        l = ThreadPoolListener(callback, max_workers)
        self.register_listener(l)
        return l
