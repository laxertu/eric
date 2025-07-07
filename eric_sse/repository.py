from abc import ABC, abstractmethod

from eric_sse.listener import MessageQueueListener
from eric_sse.queue import Queue, InMemoryQueue


class AbstractMessageQueueRepository(ABC):
    """
    Abstraction for queues creation

    see :class:`eric_sse.entities.AbstractChannel`
    """
    @abstractmethod
    async def create(self) -> Queue:
        ...

    @abstractmethod
    async def persist(self, listeners: list[MessageQueueListener], queues: dict[str, Queue]) -> None:
        """
        :param listeners: listeners to persist
        :param queues: queues to persist. A dictionary where keys are correspondant listeners ids and values are Queue

        * If some key of queues do not match with some listener in listeners, then they will be created. see create() method

        * If some listeners in listeners do not match with some queues, then they will *not* be persisted
        """
        ...

    @abstractmethod
    async def load(self) -> (list[MessageQueueListener], dict[str: Queue]):
        ...

    @abstractmethod
    async def delete(self, listener_id: str):
        ...


class InMemoryMessageQueueRepository(AbstractMessageQueueRepository):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    async def create(self) -> Queue:
        return InMemoryQueue()

    async def persist(self, listeners: list[MessageQueueListener], queues: dict[str, Queue]) -> None:
        pass

    async def load(self) -> (list[MessageQueueListener], dict[str: Queue]):
        return [], {}

    async def delete(self, listener_id: str):
        pass
