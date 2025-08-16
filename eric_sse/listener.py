import eric_sse
from eric_sse.message import MessageContract


logger = eric_sse.get_logger()

class MessageQueueListener:
    """
    Base class for listeners.

    Optionally you can override on_message method if you need to inject code at message delivery time.
    """

    def __init__(self, listener_id: str | None = None):
        self.id: str = listener_id if listener_id else eric_sse.generate_uuid()
        self.__is_running: bool = False

    def on_message(self, msg: MessageContract) -> None:
        """Event handler. It executes when a message is delivered to client"""
        pass

    def start(self) -> None:
        self.__is_running = True

    def stop(self) -> None:
        self.__is_running = False

    def is_running(self) -> bool:
        return self.__is_running

