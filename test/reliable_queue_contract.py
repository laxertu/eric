import asyncio
import time
from abc import ABC, abstractmethod
from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.entities import AbstractChannel
from eric_sse.exception import NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.queue_patterns import ReliableMessage, ReliableQueue
from eric_sse.repository import ChannelRepository


class ReliableQueueContract(ABC):
    """
    Use cases every :class:`~eric_sse.queue_patterns.ReliableQueue` setup has to satisfy, whatever its inner queue
    and in-flight storage.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder` whose queues are reliable queues with the
    given visibility timeout::

        class RedisReliableQueueTestCase(ReliableQueueContract, IsolatedAsyncioTestCase):
            def create_builder(self, visibility_timeout):
                return ChannelRepositoryBuilder(SSEChannel, RedisStorage()).queues(
                    lambda: ReliableQueue(RedisQueue(), visibility_timeout=visibility_timeout, in_flight=RedisStorage())
                )

            def channel_data(self):
                return {}

    Concrete classes must be ``IsolatedAsyncioTestCase``, as some use cases are async.
    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self, visibility_timeout: float | None) -> ChannelRepositoryBuilder:
        """Returns the builder under test, creating reliable queues with **visibility_timeout**."""
        pass

    @abstractmethod
    def channel_data(self) -> dict:
        """Returns the data passed to the built repository's ``create``, see ``ChannelRepositoryContract``."""
        pass

    def _subscribe(self, visibility_timeout: float | None = 30.0) -> tuple[ChannelRepository, AbstractChannel, MessageQueueListener]:
        repository = self.create_builder(visibility_timeout).build()
        channel = repository.create(self.channel_data())
        listener = channel.add_listener()
        listener.start()
        return repository, channel, listener

    @staticmethod
    def _queue_of(channel: AbstractChannel, listener: MessageQueueListener) -> ReliableQueue:
        return next(connection.queue for connection in channel.get_connections() if connection.listener.id == listener.id)

    def test_delivered_message_stays_in_flight_until_acknowledged(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe()
        channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hello'))

        msg = channel.deliver_next(listener.id)

        self.assertIsInstance(msg, ReliableMessage)
        self.assertEqual(('test', 'hello', 1), (msg.type, msg.payload, msg.deliveries))
        self.assertEqual([msg.id], [m.id for m in self._queue_of(channel, listener).in_flight()])
        with self.assertRaises(NoMessagesException):
            channel.deliver_next(listener.id)

    def test_acknowledged_message_is_never_delivered_again(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=0)
        queue = self._queue_of(channel, listener)
        channel.dispatch(listener.id, Message(msg_type='test'))
        msg = channel.deliver_next(listener.id)

        self.assertTrue(queue.ack(msg.id))

        self.assertFalse(queue.ack(msg.id))
        self.assertEqual([], queue.in_flight())
        self.assertEqual(0, queue.requeue_expired())
        with self.assertRaises(NoMessagesException):
            channel.deliver_next(listener.id)

    def test_rejected_message_is_delivered_again_after_waiting_ones(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe()
        queue = self._queue_of(channel, listener)
        channel.dispatch(listener.id, Message(msg_type='first'))
        channel.dispatch(listener.id, Message(msg_type='second'))
        first = channel.deliver_next(listener.id)

        self.assertTrue(queue.nack(first.id))

        self.assertFalse(queue.nack(first.id))
        self.assertEqual('second', channel.deliver_next(listener.id).type)
        redelivered = channel.deliver_next(listener.id)
        self.assertEqual((first.id, 'first', 2), (redelivered.id, redelivered.type, redelivered.deliveries))

    def test_unknown_messages_cannot_be_acknowledged_or_rejected(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe()
        queue = self._queue_of(channel, listener)

        self.assertFalse(queue.ack('unknown'))
        self.assertFalse(queue.nack('unknown'))

    def test_message_not_acknowledged_in_time_is_delivered_again(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=0.01)
        channel.dispatch(listener.id, Message(msg_type='test'))
        msg = channel.deliver_next(listener.id)

        time.sleep(0.02)

        redelivered = channel.deliver_next(listener.id)
        self.assertEqual((msg.id, 2), (redelivered.id, redelivered.deliveries))

    def test_late_acknowledgement_does_not_cancel_redelivery(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=0.01)
        queue = self._queue_of(channel, listener)
        channel.dispatch(listener.id, Message(msg_type='test'))
        msg = channel.deliver_next(listener.id)
        time.sleep(0.02)

        self.assertEqual(1, queue.requeue_expired())

        self.assertFalse(queue.ack(msg.id))
        self.assertEqual(msg.id, channel.deliver_next(listener.id).id)

    def test_message_within_visibility_timeout_stays_in_flight(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=60)
        queue = self._queue_of(channel, listener)
        channel.dispatch(listener.id, Message(msg_type='test'))
        channel.deliver_next(listener.id)

        self.assertEqual(0, queue.requeue_expired())
        self.assertEqual(1, len(queue.in_flight()))

    def test_without_visibility_timeout_only_rejection_redelivers(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=None)
        queue = self._queue_of(channel, listener)
        channel.dispatch(listener.id, Message(msg_type='test'))
        msg = channel.deliver_next(listener.id)

        self.assertEqual(0, queue.requeue_expired())

        self.assertTrue(queue.nack(msg.id))
        self.assertEqual(msg.id, channel.deliver_next(listener.id).id)

    async def test_waiting_listener_receives_message_dispatched_later(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe()
        waiting = asyncio.create_task(channel.wait_next(listener.id, timeout=1))
        await asyncio.sleep(0)
        channel.dispatch(listener.id, Message(msg_type='test'))

        msg = await waiting

        self.assertEqual(('test', 1), (msg.type, msg.deliveries))
        self.assertEqual([msg.id], [m.id for m in self._queue_of(channel, listener).in_flight()])

    async def test_waiting_listener_receives_message_not_acknowledged_in_time(self: 'ReliableQueueContract | TestCase'):
        _, channel, listener = self._subscribe(visibility_timeout=0.01)
        channel.dispatch(listener.id, Message(msg_type='test'))
        msg = await channel.wait_next(listener.id, timeout=1)
        await asyncio.sleep(0.02)

        self.assertEqual(msg.id, (await channel.wait_next(listener.id, timeout=1)).id)

    def test_messages_in_flight_and_waiting_survive_reload(self: 'ReliableQueueContract | TestCase'):
        repository, channel, listener = self._subscribe()
        channel.dispatch(listener.id, Message(msg_type='first'))
        channel.dispatch(listener.id, Message(msg_type='second'))
        first = channel.deliver_next(listener.id)
        repository.persist(channel)

        loaded = repository.load_one(channel.id)
        loaded_listener = loaded.get_listener(listener.id)
        loaded_listener.start()

        self.assertTrue(self._queue_of(loaded, loaded_listener).ack(first.id))
        self.assertEqual('second', loaded.deliver_next(listener.id).type)
