from abc import ABC, abstractmethod
from threading import Lock

from eric_sse.message import Message
from eric_sse.exception import NoMessagesException


class Queue(ABC):
    @abstractmethod
    def pop(self) -> Message:
        ...

    @abstractmethod
    def push(self, message: Message) -> None:
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


class AbstractMessageQueueFactory(ABC):
    @abstractmethod
    def create(self) -> Queue:
        ...


class InMemoryMessageQueueFactory(AbstractMessageQueueFactory):
    def create(self) -> Queue:
        return InMemoryQueue()
