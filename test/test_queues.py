import asyncio
import threading
import time
from unittest import TestCase, IsolatedAsyncioTestCase

from eric_sse.connection import Connection
from eric_sse.exception import NoMessagesException, StoppedListenerException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.queues import Queue, InMemoryQueue
from test.mock.channel import FakeChannel
from test.mock.listener import MessageQueueListenerMock


def push_later(queue: Queue, message: MessageContract, delay: float = 0.05):
    """Pushes from another thread, like a dispatch made outside the event loop."""
    threading.Timer(delay, queue.push, args=(message,)).start()


class InMemoryQueuePopTestCase(TestCase):

    def test_pop_without_timeout_returns_immediately(self):
        with self.assertRaises(NoMessagesException):
            InMemoryQueue().pop()

    def test_pop_waits_up_to_timeout(self):
        sut = InMemoryQueue()
        push_later(sut, Message(msg_type='late'))
        self.assertEqual('late', sut.pop(timeout=2).type)

        start = time.monotonic()
        with self.assertRaises(NoMessagesException):
            sut.pop(timeout=0.05)
        self.assertGreaterEqual(time.monotonic() - start, 0.05)


class InMemoryQueueWaitPopTestCase(IsolatedAsyncioTestCase):

    async def test_returns_queued_message(self):
        sut = InMemoryQueue()
        sut.push(Message(msg_type='queued'))
        self.assertEqual('queued', (await sut.wait_pop(1)).type)

    async def test_wakes_up_on_push_from_event_loop(self):
        sut = InMemoryQueue()
        asyncio.get_running_loop().call_later(0.05, sut.push, Message(msg_type='late'))
        self.assertEqual('late', (await sut.wait_pop(2)).type)

    async def test_wakes_up_on_push_from_another_thread(self):
        sut = InMemoryQueue()
        push_later(sut, Message(msg_type='late'))
        self.assertEqual('late', (await sut.wait_pop(2)).type)

    async def test_timeout(self):
        with self.assertRaises(NoMessagesException):
            await InMemoryQueue().wait_pop(0.05)

    async def test_consecutive_waits_deliver_messages_in_order(self):
        sut = InMemoryQueue()
        loop = asyncio.get_running_loop()
        loop.call_later(0.05, sut.push, Message(msg_type='first'))
        loop.call_later(0.05, sut.push, Message(msg_type='second'))

        self.assertEqual('first', (await sut.wait_pop(2)).type)
        self.assertEqual('second', (await sut.wait_pop(2)).type)
        with self.assertRaises(NoMessagesException):
            await sut.wait_pop(0.05)

    async def test_message_arrived_at_timeout_is_returned(self):
        # A push whose wake-up hasn't run yet when the timeout fires: the message is queued, the waiter isn't resolved
        sut = InMemoryQueue()
        pending_push = sut._InMemoryQueue__queue
        asyncio.get_running_loop().call_later(0.01, pending_push.put, Message(msg_type='late'))

        self.assertEqual('late', (await sut.wait_pop(0.05)).type)

    async def test_push_after_timeout_is_kept_for_next_wait(self):
        sut = InMemoryQueue()
        with self.assertRaises(NoMessagesException):
            await sut.wait_pop(0.05)
        sut.push(Message(msg_type='later'))
        self.assertEqual('later', (await sut.wait_pop(1)).type)


class SyncOnlyQueue(Queue):
    """A queue implementing only the abstract methods, like a third party backend."""
    def __init__(self):
        self.inner = InMemoryQueue()

    def pop(self, timeout: float = 0) -> MessageContract:
        return self.inner.pop(timeout)

    def push(self, message: MessageContract) -> None:
        self.inner.push(message)


class DefaultWaitPopTestCase(IsolatedAsyncioTestCase):

    async def test_waits_in_a_thread_without_blocking_the_loop(self):
        sut = SyncOnlyQueue()
        task = asyncio.create_task(sut.wait_pop(2))
        # The loop is free while the queue waits
        await asyncio.sleep(0.05)
        self.assertFalse(task.done())
        sut.push(Message(msg_type='late'))
        self.assertEqual('late', (await task).type)

    async def test_timeout(self):
        with self.assertRaises(NoMessagesException):
            await SyncOnlyQueue().wait_pop(0.05)


class ChannelStreamWaitTestCase(IsolatedAsyncioTestCase):

    async def test_wait_next(self):
        channel = FakeChannel()
        listener = channel.add_listener()

        with self.assertRaises(StoppedListenerException):
            await channel.wait_next(listener.id, 0.05)  # Listener not running

        listener.start()
        asyncio.get_running_loop().call_later(0.05, channel.dispatch, listener.id, Message(msg_type='late'))
        self.assertEqual('late', (await channel.wait_next(listener.id, 2)).type)

    async def test_stream_delivers_messages_dispatched_while_waiting(self):
        channel = FakeChannel()
        listener = MessageQueueListenerMock(num_messages_before_disconnect=2)
        channel.register_listener(listener)
        listener.start()

        loop = asyncio.get_running_loop()
        loop.call_later(0.05, channel.dispatch, listener.id, Message(msg_type='first'))
        loop.call_later(0.1, channel.dispatch, listener.id, Message(msg_type='second'))

        received = [m.type async for m in channel.message_stream(listener)]
        self.assertEqual(['first', 'second'], received)

    async def test_stream_ends_when_listener_is_stopped_while_idle(self):
        channel = FakeChannel()
        channel.wait_timeout_seconds = 0.05
        listener = channel.add_listener()
        listener.start()
        asyncio.get_running_loop().call_later(0.05, listener.stop)

        received = [m async for m in channel.message_stream(listener)]
        self.assertEqual([], received)


class StoppedAfterCheckListener(MessageQueueListener):
    """Running for the stream loop check, stopped when the channel waits: as if stopped by another thread in between."""
    def __init__(self):
        super().__init__()
        self.answers = iter([True])

    def is_running(self) -> bool:
        return next(self.answers, False)


class StoppedListenerStreamTestCase(IsolatedAsyncioTestCase):

    async def test_stream_yields_error_and_ends(self):
        channel = FakeChannel()
        listener = StoppedAfterCheckListener()
        channel.register_connection(Connection(listener=listener, queue=InMemoryQueue()))

        events = [event async for event in channel.message_stream(listener)]

        self.assertEqual(1, len(events))
        self.assertIsInstance(events[0], StoppedListenerException)
