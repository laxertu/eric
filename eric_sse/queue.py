from abc import ABC, abstractmethod
from asyncio import Lock

from eric_sse.message import MessageContract
from eric_sse.exception import NoMessagesException


class Queue(ABC):
    """Abstract base class for queues (FIFO)"""
    @abstractmethod
    async def pop(self) -> MessageContract:
        """
        Next message from the queue.

        Raises a :class:`eric_sse.exception.NoMessagesException` if the queue is empty.
        """
        ...

    @abstractmethod
    async def push(self, message: MessageContract) -> None:
        ...

    @abstractmethod
    async def delete(self) -> None:
        """Removes all messages from the queue."""
        ...

class InMemoryQueue(Queue):
    def __init__(self):
        self.__messages: list[MessageContract] = []

    async def pop(self) -> MessageContract:
        try:
            lock = Lock()
            async with lock:
                m = self.__messages.pop(0)
                return m
        except IndexError:
            raise NoMessagesException

    async def push(self, message: MessageContract) -> None:
        self.__messages.append(message)

    async def delete(self) -> None:
        self.__messages = []


