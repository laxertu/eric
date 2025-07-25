from abc import ABC, abstractmethod
from typing import AsyncIterable, Tuple

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
    async def persist(self, listener: MessageQueueListener, queue: Queue) -> None:
        ...

    @abstractmethod
    async def load(self) -> AsyncIterable[Tuple[MessageQueueListener, Queue]]:
        """
        Returns a list of persisted listeners and a dictionary of queues indexed by the ids of those listeners
        """
        ...

    @abstractmethod
    async def delete(self, listener_id: str) -> None:
        ...


class InMemoryMessageQueueRepository(AbstractMessageQueueRepository):
    """
    Default implementation used by :class:`eric_sse.entities.AbstractChannel`
    """
    async def create(self) -> Queue:
        return InMemoryQueue()

    async def persist(self, listeners: list[MessageQueueListener], queues: dict[str, Queue]) -> None:
        pass

    async def load(self) ->  AsyncIterable[Tuple[MessageQueueListener, Queue]]:
        pass

    async def delete(self, listener_id: str) -> None:
        pass
