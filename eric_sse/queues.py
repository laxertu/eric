from abc import ABC, abstractmethod
from queue import SimpleQueue, Empty, Full

from eric_sse.message import MessageContract
from eric_sse.exception import NoMessagesException, RepositoryError


class Queue(ABC):
    """Abstract base class for queues (FIFO)."""

    @abstractmethod
    def pop(self) -> MessageContract:
        """
        Next message from the queue.

        Raises a :class:`~eric_sse.exception.NoMessagesException` if the queue is empty.
        """
        ...

    @abstractmethod
    def push(self, message: MessageContract) -> None:
        ...

class InMemoryQueue(Queue):
    """In memory implementation."""
    def __init__(self):
        super().__init__()
        self.__messages: list[MessageContract] = []
        self.__queue: SimpleQueue = SimpleQueue()

    def pop(self) -> MessageContract:
        try:
            m = self.__queue.get(block=False)
            return m
        except Empty:
            raise NoMessagesException

    def push(self, message: MessageContract) -> None:
        try:
            self.__queue.put(message)
        except Full as e:
            raise RepositoryError(e)

