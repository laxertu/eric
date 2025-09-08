from abc import ABC, abstractmethod
from eric_sse.message import MessageContract

from eric_sse import get_logger
logger = get_logger()

class QueuingErrorHandler:

    def handle_push_error(self, msg: MessageContract, exception: Exception):
        pass
    def handle_pop_error(self, exception: Exception):
        pass

class ListenerErrorHandler(ABC):
    @abstractmethod
    def handle_on_message_error(self, msg: MessageContract, exception: Exception):
        pass
