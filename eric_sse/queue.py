from abc import ABC, abstractmethod
from threading import Lock

from eric_sse.message import Message
from eric_sse.exception import NoMessagesException

class RepositoryError(Exception):
    ...

class Queue(ABC):
    @abstractmethod
    def pop(self) -> Message:
        ...

    @abstractmethod
    def push(self, message: Message) -> None:
        ...

    @abstractmethod
    def delete(self) -> None:
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
