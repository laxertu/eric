"""
Profiling decorators for queues and listeners.

They wrap an existing queue or listener, delegate every call to it, and measure how many times its main methods
are called and how long they take::

    queue = ProfiledQueue(InMemoryQueue())
    listener = ProfiledListener(MyListener())
    channel.register_connection(Connection(listener=listener, queue=queue))
    ...
    print(queue.push_stats.calls, queue.push_stats.total_time, listener.on_message_stats.mean_time)
"""
import threading
import time
from typing import Any, TYPE_CHECKING

from eric_sse.exception import NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import M, MIn, MOut
from eric_sse.queues import Queue

if TYPE_CHECKING:
    from eric_sse.entities import AbstractChannel


class CallStats:
    """Number of calls of a method and the total time they took, in seconds. Calls that raise are counted too."""

    def __init__(self) -> None:
        self.__calls: int = 0
        self.__total_time: float = 0.0
        self.__lock = threading.Lock()

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        del state['_CallStats__lock']
        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)
        self.__lock = threading.Lock()

    def record(self, elapsed: float) -> None:
        """Adds a call that took **elapsed** seconds."""
        with self.__lock:
            self.__calls += 1
            self.__total_time += elapsed

    @property
    def calls(self) -> int:
        return self.__calls

    @property
    def total_time(self) -> float:
        """Total time of all calls, in seconds."""
        return self.__total_time

    @property
    def mean_time(self) -> float:
        """Mean time per call, in seconds. 0 if there were no calls."""
        return self.__total_time / self.__calls if self.__calls else 0.0


class ProfiledQueue(Queue[MIn, MOut]):
    """
    Wraps a queue and profiles its :meth:`push`, :meth:`pop` and :meth:`wait_pop`.

    Times include waiting: a :meth:`wait_pop` or a :meth:`pop` with a timeout lasts until a message arrives,
    or the timeout expires. Empty pops raising a :class:`~eric_sse.exception.NoMessagesException` are counted too.

    :param ~eric_sse.queues.Queue queue: The profiled queue.
    """

    def __init__(self, queue: Queue[MIn, MOut]) -> None:
        self.__queue = queue
        self.__push_stats = CallStats()
        self.__pop_stats = CallStats()
        self.__wait_pop_stats = CallStats()

    @property
    def queue(self) -> Queue[MIn, MOut]:
        """The profiled queue."""
        return self.__queue

    @property
    def push_stats(self) -> CallStats:
        return self.__push_stats

    @property
    def pop_stats(self) -> CallStats:
        return self.__pop_stats

    @property
    def wait_pop_stats(self) -> CallStats:
        return self.__wait_pop_stats

    def push(self, message: MIn) -> None:
        start = time.perf_counter()
        try:
            self.__queue.push(message)
        finally:
            self.__push_stats.record(time.perf_counter() - start)

    def pop(self, timeout: float = 0) -> MOut:
        start = time.perf_counter()
        try:
            message = self.__queue.pop(timeout)
        finally:
            self.__pop_stats.record(time.perf_counter() - start)
        return message

    async def wait_pop(self, timeout: float) -> MOut:
        start = time.perf_counter()
        try:
            message = await self.__queue.wait_pop(timeout)
        finally:
            self.__wait_pop_stats.record(time.perf_counter() - start)
        return message


class ProfiledListener(MessageQueueListener[M]):
    """
    Wraps a listener and profiles its :meth:`on_message`.

    It has the same id as the profiled listener, and delegates every other call to it.

    :param ~eric_sse.listener.MessageQueueListener listener: The profiled listener.
    """

    def __init__(self, listener: MessageQueueListener[M]) -> None:
        super().__init__(listener_id=listener.id)
        self.__listener = listener
        self.__on_message_stats = CallStats()

    @property
    def listener(self) -> MessageQueueListener[M]:
        """The profiled listener."""
        return self.__listener

    @property
    def on_message_stats(self) -> CallStats:
        return self.__on_message_stats

    def on_message(self, msg: M) -> None:
        start = time.perf_counter()
        try:
            self.__listener.on_message(msg)
        finally:
            self.__on_message_stats.record(time.perf_counter() - start)

    def on_registered(self, channel: 'AbstractChannel[Any, M]') -> None:
        self.__listener.on_registered(channel)

    def start(self) -> None:
        self.__listener.start()

    def stop(self) -> None:
        self.__listener.stop()

    def is_running(self) -> bool:
        return self.__listener.is_running()
