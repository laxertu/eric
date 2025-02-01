from abc import ABC, abstractmethod
from threading import Lock

from eric_sse.message import Message
from eric_sse.exception import NoMessagesException


class Queue(ABC):
    """Abstract base class for queues."""
    @abstractmethod
    def pop(self) -> Message:
        ...

    @abstractmethod
    def push(self, message: Message) -> None:
        ...

    @abstractmethod
    def delete(self) -> None:
        """Removes all messages from the queue."""
        ...

class InMemoryQueue(Queue):
    def __init__(self):
        self.__messages: list[Message] = []

    def pop(self) -> Message:
        try:
            with Lock():
                return self.__messages.pop(0)
        except IndexError:
            raise NoMessagesException

    def push(self, message: Message) -> None:
        self.__messages.append(message)

    def delete(self) -> None:
        self.__messages = []

class AbstractMessageQueueFactory(ABC):
    """
    Abstraction for queues creation

    see :class:`eric_sse.entities.AbstractChannel`
    """
    @abstractmethod
    def create(self) -> Queue:
        ...


class InMemoryMessageQueueFactory(AbstractMessageQueueFactory):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    def create(self) -> Queue:
        return InMemoryQueue()


class RepositoryError(Exception):
    """
    Raised when an unexpected error occurs while trying to fetch messages from a queue.

    Concrete implementations of :class:`Queue` should wrap here the unexpected exceptions they catch before raising, and
    an :class:`eric_sse.exception.NoMessagesException` when a pop is requested on an empty queue.
    """
    ...