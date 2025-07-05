from abc import ABC, abstractmethod
from threading import Lock

from eric_sse.message import MessageContract
from eric_sse.exception import NoMessagesException


class Queue(ABC):
    """Abstract base class for queues (FIFO)"""
    @abstractmethod
    def pop(self) -> MessageContract:
        """
        Next message from the queue.

        Raises a :class:`eric_sse.exception.NoMessagesException` if the queue is empty.
        """
        ...

    @abstractmethod
    def push(self, message: MessageContract) -> None:
        ...

    @abstractmethod
    def delete(self) -> None:
        """Removes all messages from the queue."""
        ...

class InMemoryQueue(Queue):
    def __init__(self):
        self.__messages: list[MessageContract] = []

    def pop(self) -> MessageContract:
        """
        """
        try:
            with Lock():
                return self.__messages.pop(0)
        except IndexError:
            raise NoMessagesException

    def push(self, message: MessageContract) -> None:
        self.__messages.append(message)

    def delete(self) -> None:
        self.__messages = []


