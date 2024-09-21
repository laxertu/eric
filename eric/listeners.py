from collections.abc import Callable
from sys import executable

from eric.entities import MessageQueueListener, Message
from logging import Logger

class LoggingListener(MessageQueueListener):

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger

    def on_message(self, msg: Message) -> None:
        self.logger.log(level=int(msg.type), msg=msg.payload)



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