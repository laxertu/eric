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
    def persist(self, listeners: list[MessageQueueListener], queues: dict[str, Queue]) -> None:
        """
        :param listeners: listeners to persist
        :param queues: queues to persist. A dictionary where keys are correspondant listeners ids and values are Queue

        * If some key of queues do not match with some listener in listeners, then they will be created. see create() method

        * If some listeners in listeners do not match with some queues, then they will *not* be persisted
        """
        ...

    @abstractmethod
    def load(self) -> (dict[str, MessageQueueListener], dict[str: Queue]):
        ...

    @abstractmethod
    def delete(self, listener_id: str):
        ...


class InMemoryMessageQueueRepository(AbstractMessageQueueRepository):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    def create(self) -> Queue:
        return InMemoryQueue()

    def persist(self, listeners: dict[str, MessageQueueListener], queues: dict[str: Queue]) -> None:
        pass

    def load(self) -> (dict[str, MessageQueueListener], dict[str, Queue]):
        return {}, {}

    def delete(self, listener_id: str):
        pass

