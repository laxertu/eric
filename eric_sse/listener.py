from abc import ABC

import eric_sse
from eric_sse.message import MessageContract

logger = eric_sse.get_logger()

class MessageQueueListener(ABC):
    """
    Base class for listeners.

    Optionally you can override on_message method if you need to inject code at message delivery time.
    """

    def __init__(self):
        self.id: str = eric_sse.generate_uuid()
        self.__is_running: bool = False

    async def start(self) -> None:
        self.start_sync()

    def start_sync(self) -> None:
        logger.debug(f"Starting listener {self.id}")
        self.__is_running = True

    async def is_running(self) -> bool:
        return self.is_running_sync()

    def is_running_sync(self) -> bool:
        return self.__is_running

    async def stop(self) -> None:
        self.stop_sync()

    def stop_sync(self) -> None:
        logger.debug(f"Stopping listener {self.id}")
        self.__is_running = False

    async def on_message(self, msg: MessageContract) -> None:
        """Event handler. It executes when a message is delivered to client"""
        pass
