import asyncio
from abc import ABC, abstractmethod
from queue import SimpleQueue, Empty, Full
from typing import Generic

from eric_sse.message import M, MIn, MOut
from eric_sse.exception import NoMessagesException, RepositoryError, TimeoutException


class Queue(ABC, Generic[MIn, MOut]):
    """
    Abstract base class for queues (FIFO).

    Generic on the type of messages pushed (**MIn**) and popped (**MOut**), e.g. ``Queue[SignedMessage, SignedMessage]``.
    They differ when a queue transforms messages, as :class:`~eric_sse.queue_patterns.ReliableQueue` does.
    Plain ``Queue`` holds any message.

    Implementations must provide :meth:`pop` and :meth:`push`. Override :meth:`wait_pop` too if the backend
    can wait for messages without blocking a thread, as :class:`~eric_sse.queues.InMemoryQueue` does.
    """

    @abstractmethod
    def pop(self, timeout: float = 0) -> MOut:
        """
        Next message from the queue.

        :param timeout: Seconds to wait for a message. With 0 it returns immediately.

        Raises a :class:`~eric_sse.exception.NoMessagesException` if no message is available: implementations should
        raise its subclass :class:`~eric_sse.exception.TimeoutException` when they waited, i.e. **timeout** > 0.
        """
        ...

    @abstractmethod
    def push(self, message: MIn) -> None:
        ...

    async def wait_pop(self, timeout: float) -> MOut:
        """
        Waits for the next message without blocking the event loop.

        The default implementation runs :meth:`pop` with **timeout** in a worker thread, so it takes one thread
        per waiting call. Override it with a native async wait when possible.

        :param timeout: Seconds to wait for a message.

        Raises a :class:`~eric_sse.exception.TimeoutException` if no message arrives within **timeout**.
        """
        try:
            return await asyncio.to_thread(self.pop, timeout)
        except NoMessagesException:
            # pop() implementations may raise a plain NoMessagesException when they time out
            raise TimeoutException from None


def _resolve(waiter: asyncio.Future) -> None:
    if not waiter.done():
        waiter.set_result(None)


class InMemoryQueue(Queue[M, M]):
    """
    In memory implementation. Not durable: its messages live in the current process only.

    It has a single consumer, as a queue belongs to one listener: concurrent :meth:`wait_pop` calls on the same
    queue are not supported. :meth:`wait_pop` waits natively, without threads or polling.
    :meth:`push` can be called from any thread.

    It can't be serialised (e.g. pickled), so it can only be persisted with storages that keep objects
    in process, such as :class:`~eric_sse.repository.InMemoryStorage`.
    """
    def __init__(self):
        super().__init__()
        self.__queue: SimpleQueue = SimpleQueue()
        self.__waiter: tuple[asyncio.AbstractEventLoop, asyncio.Future] | None = None

    def pop(self, timeout: float = 0) -> M:
        try:
            return self.__queue.get(block=timeout > 0, timeout=timeout if timeout > 0 else None)
        except Empty:
            raise (TimeoutException if timeout > 0 else NoMessagesException) from None

    def push(self, message: M) -> None:
        try:
            self.__queue.put(message)
        except Full as e:
            raise RepositoryError(e)

        waiter = self.__waiter
        if waiter is not None:
            loop, future = waiter
            try:
                loop.call_soon_threadsafe(_resolve, future)
            except RuntimeError:
                # Loop already closed
                pass

    async def wait_pop(self, timeout: float) -> M:
        try:
            return self.pop()
        except NoMessagesException:
            pass

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.__waiter = (loop, future)
        try:
            # Checks again: a push between the first pop and the waiter registration would be missed otherwise
            try:
                return self.pop()
            except NoMessagesException:
                pass
            try:
                await asyncio.wait_for(future, timeout)
            except asyncio.TimeoutError:
                # A message may have arrived anyway, with its wake-up still pending: the queue decides
                try:
                    return self.pop()
                except NoMessagesException:
                    raise TimeoutException from None
            # Single consumer: the message that woke us up is still there
            return self.pop()
        finally:
            self.__waiter = None
