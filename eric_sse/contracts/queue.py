import asyncio
import threading
import time
from abc import ABC, abstractmethod
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.entities import AbstractChannel
from eric_sse.exception import NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract


class StopsAfterTwoMessages(MessageQueueListener):
    def __init__(self):
        super().__init__()
        self.received: list[str] = []

    def on_message(self, msg: MessageContract) -> None:
        self.received.append(msg.type)
        if len(self.received) == 2:
            self.stop()


class QueueContract(ABC):
    """
    Use cases every :class:`~eric_sse.queues.Queue` implementation has to satisfy.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder` creating queues of the class under test::

        class RedisQueueTestCase(QueueContract, IsolatedAsyncioTestCase):
            def create_builder(self):
                return ChannelRepositoryBuilder(SSEChannel).queues(RedisQueue)

            def channel_data(self):
                return {}

    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self) -> ChannelRepositoryBuilder:
        """Returns the builder under test. Called once per test."""
        pass

    @abstractmethod
    def channel_data(self) -> dict:
        """Returns the data passed to the built repository's ``create``, see ``ChannelRepositoryContract``."""
        pass

    def _subscribe(self, builder: ChannelRepositoryBuilder | None = None) -> tuple[AbstractChannel, Connection]:
        builder = builder if builder is not None else self.create_builder()
        channel = builder.build().create(self.channel_data())
        connection = channel.add_connection()
        connection.listener.start()
        return channel, connection

    def test_empty_queue_answers_immediately_without_a_timeout(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()

        with self.assertRaises(NoMessagesException):
            channel.deliver_next(connection.id)

    def test_messages_are_delivered_in_dispatch_order(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        channel.dispatch(connection.id, Message(msg_type='first'))
        channel.dispatch(connection.id, Message(msg_type='second'))

        self.assertEqual('first', channel.deliver_next(connection.id).type)
        self.assertEqual('second', channel.deliver_next(connection.id).type)

    def test_pop_waits_for_a_message_up_to_its_timeout(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        threading.Timer(0.05, channel.dispatch, args=(connection.id, Message(msg_type='late'))).start()

        self.assertEqual('late', connection.queue.pop(timeout=2).type)

        start = time.monotonic()
        with self.assertRaises(NoMessagesException):
            connection.queue.pop(timeout=0.05)
        self.assertGreaterEqual(time.monotonic() - start, 0.05)

    async def test_waiting_returns_a_message_already_queued(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        channel.dispatch(connection.id, Message(msg_type='queued'))

        self.assertEqual('queued', (await channel.wait_next(connection.id, 1)).type)

    async def test_waiting_receives_a_message_dispatched_from_the_event_loop(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        asyncio.get_running_loop().call_later(0.05, channel.dispatch, connection.id, Message(msg_type='late'))
        start = time.monotonic()

        self.assertEqual('late', (await channel.wait_next(connection.id, 2)).type)
        self.assertLess(time.monotonic() - start, 1)  # Woken up by the message, not by the timeout

    async def test_waiting_receives_a_message_dispatched_from_another_thread(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        threading.Timer(0.05, channel.dispatch, args=(connection.id, Message(msg_type='late'))).start()
        start = time.monotonic()

        self.assertEqual('late', (await channel.wait_next(connection.id, 2)).type)
        self.assertLess(time.monotonic() - start, 1)  # Woken up by the message, not by the timeout

    async def test_waiting_gives_up_after_its_timeout(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()

        with self.assertRaises(NoMessagesException):
            await channel.wait_next(connection.id, 0.05)

    async def test_consecutive_waits_receive_messages_in_order(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        loop = asyncio.get_running_loop()
        loop.call_later(0.05, channel.dispatch, connection.id, Message(msg_type='first'))
        loop.call_later(0.05, channel.dispatch, connection.id, Message(msg_type='second'))

        self.assertEqual('first', (await channel.wait_next(connection.id, 2)).type)
        self.assertEqual('second', (await channel.wait_next(connection.id, 2)).type)
        with self.assertRaises(NoMessagesException):
            await channel.wait_next(connection.id, 0.05)

    async def test_message_dispatched_after_a_timeout_is_kept_for_the_next_wait(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        with self.assertRaises(NoMessagesException):
            await channel.wait_next(connection.id, 0.05)

        channel.dispatch(connection.id, Message(msg_type='later'))

        self.assertEqual('later', (await channel.wait_next(connection.id, 1)).type)

    async def test_waiting_does_not_block_the_event_loop(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        waiting = asyncio.create_task(channel.wait_next(connection.id, 2))

        await asyncio.sleep(0.05)

        self.assertFalse(waiting.done())
        channel.dispatch(connection.id, Message(msg_type='late'))
        self.assertEqual('late', (await waiting).type)

    async def test_stream_delivers_messages_dispatched_while_waiting(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe(self.create_builder().listeners(StopsAfterTwoMessages))
        loop = asyncio.get_running_loop()
        loop.call_later(0.05, channel.dispatch, connection.id, Message(msg_type='first'))
        loop.call_later(0.1, channel.dispatch, connection.id, Message(msg_type='second'))

        events = [event async for event in channel.message_stream(connection.id)]

        self.assertEqual(2, len(events))
        self.assertEqual(['first', 'second'], connection.listener.received)

    async def test_stream_ends_when_the_listener_stops_while_idle(self: 'QueueContract | IsolatedAsyncioTestCase'):
        channel, connection = self._subscribe()
        channel.wait_timeout_seconds = 0.05
        asyncio.get_running_loop().call_later(0.05, connection.listener.stop)

        self.assertEqual([], [event async for event in channel.message_stream(connection.id)])
