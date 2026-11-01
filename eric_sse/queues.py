import asyncio
import threading
from abc import ABC, abstractmethod
from queue import SimpleQueue, Empty, Full

from eric_sse.message import MessageContract
from eric_sse.exception import NoMessagesException, RepositoryError


class Queue(ABC):
    """
    Abstract base class for queues (FIFO).

    Implementations must provide :meth:`pop` and :meth:`push`. Override :meth:`wait_pop` too if the backend
    can wait for messages without blocking a thread, as :class:`~eric_sse.queues.InMemoryQueue` does.
    """

    @abstractmethod
    def pop(self, timeout: float = 0) -> MessageContract:
        """
        Next message from the queue.

        :param timeout: Seconds to wait for a message. With 0 it returns immediately.

        Raises a :class:`~eric_sse.exception.NoMessagesException` if no message is available within **timeout**.
        """
        ...

    @abstractmethod
    def push(self, message: MessageContract) -> None:
        ...

    async def wait_pop(self, timeout: float) -> MessageContract:
        """
        Waits for the next message without blocking the event loop.

        The default implementation runs :meth:`pop` with **timeout** in a worker thread, so it takes one thread
        per waiting call. Override it with a native async wait when possible.

        :param timeout: Seconds to wait for a message.

        Raises a :class:`~eric_sse.exception.NoMessagesException` if no message arrives within **timeout**.
        """
        return await asyncio.to_thread(self.pop, timeout)


def _resolve(waiter: asyncio.Future) -> None:
    if not waiter.done():
        waiter.set_result(None)


class InMemoryQueue(Queue):
    """
    In memory implementation. Not durable: its messages live in the current process only.

    :meth:`wait_pop` waits natively, without threads or polling. :meth:`push` can be called from any thread.

    It can't be serialised (e.g. pickled), so it can only be persisted with storages that keep objects
    in process, such as :class:`~eric_sse.repository.InMemoryStorage`.
    """
    def __init__(self):
        super().__init__()
        self.__queue: SimpleQueue = SimpleQueue()
        self.__waiters: dict[asyncio.Future, asyncio.AbstractEventLoop] = {}
        self.__lock = threading.Lock()

    def pop(self, timeout: float = 0) -> MessageContract:
        try:
            return self.__queue.get(block=timeout > 0, timeout=timeout if timeout > 0 else None)
        except Empty:
            raise NoMessagesException

    def push(self, message: MessageContract) -> None:
        try:
            self.__queue.put(message)
        except Full as e:
            raise RepositoryError(e)
        self.__wake_waiters()

    async def wait_pop(self, timeout: float) -> MessageContract:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            try:
                return self.pop()
            except NoMessagesException:
                pass

            remaining = deadline - loop.time()
            if remaining <= 0:
                raise NoMessagesException

            waiter = loop.create_future()
            with self.__lock:
                self.__waiters[waiter] = loop
            try:
                # Checks again: a push between the first pop and the waiter registration would be missed otherwise
                try:
                    return self.pop()
                except NoMessagesException:
                    pass
                await asyncio.wait_for(waiter, remaining)
            except asyncio.TimeoutError:
                raise NoMessagesException from None
            finally:
                with self.__lock:
                    self.__waiters.pop(waiter, None)

    def __wake_waiters(self) -> None:
        with self.__lock:
            waiters = list(self.__waiters.items())
        for waiter, loop in waiters:
            try:
                loop.call_soon_threadsafe(_resolve, waiter)
            except RuntimeError:
                # Loop already closed
                pass
