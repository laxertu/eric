from abc import ABC, abstractmethod

from eric_sse.listener import MessageQueueListener
from eric_sse.queue import Queue, InMemoryQueue


class AbstractMessageQueueRepository(ABC):
    """
    Abstraction for queues creation

    see :class:`eric_sse.entities.AbstractChannel`
    """
    @abstractmethod
    def create(self) -> Queue:
        ...

    @abstractmethod
    def persist(self, listeners: dict[str: MessageQueueListener], queues: dict[str: Queue]) -> None:
        ...

    @abstractmethod
    def load(self) -> (dict[str: MessageQueueListener], dict[str: Queue]):
        ...


class InMemoryMessageQueueRepository(AbstractMessageQueueRepository):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    def create(self) -> Queue:
        return InMemoryQueue()

    def persist(self, listeners: dict[str: MessageQueueListener], queues: dict[str: Queue]) -> None:
        pass

    def load(self) -> (dict[str: MessageQueueListener], dict[str: Queue]):
        return {}, {}
