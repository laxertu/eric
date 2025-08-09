from abc import ABC, abstractmethod
from queue import SimpleQueue, Empty, Full

import eric_sse
from eric_sse.message import MessageContract
from eric_sse.exception import NoMessagesException, RepositoryError
from eric_sse.persistence import ObjectAsKeyValuePersistenceMixin


class Queue(ABC):
    """Abstract base class for queues (FIFO)."""

    @property
    @abstractmethod
    def id(self) -> str:
        ...

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

class AbstractQueue(Queue, ABC):

    def __init__(self):
        self.__id = eric_sse.generate_uuid()

    @property
    def id(self) -> str:
        return self.__id


class InMemoryQueue(AbstractQueue):

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


class PersistableQueue(AbstractQueue, ObjectAsKeyValuePersistenceMixin, ABC):
    """Concrete implementations of methods should perform in **Queues** ones their I/O operations, and define in **ObjectAsKeyValuePersistenceMixin** ones their correspondant persistence strategy"""
    ...
