import asyncio
import pickle
import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import NoMessagesException
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract, SignedMessage
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import DeadLetter, DeadLetterHandler, ReliableMessage, ReliableQueue
from eric_sse.queues import InMemoryQueue, Queue
from eric_sse.repository import InMemoryStorage
from test.mock.channel import FakeChannel
from test.test_handlers import BrokenListener, BrokenQueue, register_broken_queue


def channel_with_dead_letters(handler: DeadLetterHandler | None = None):
    channel = FakeChannel()
    dead_letters = handler if handler is not None else DeadLetterHandler()
    channel.add_queuing_error_handler(dead_letters)
    channel.add_listener_error_handler(dead_letters)
    return channel, dead_letters


class DeadLetterHandlerTestCase(IsolatedAsyncioTestCase):

    async def test_failed_push_is_dead_lettered_and_reraised(self):
        channel, dead_letters = channel_with_dead_letters()
        listener = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hello'))

        dead_letter = dead_letters.queue.pop()
        self.assertIsInstance(dead_letter, DeadLetter)
        self.assertEqual(listener.id, dead_letter.listener_id)
        self.assertEqual(('test', 'hello'), (dead_letter.type, dead_letter.payload))
        self.assertEqual("RuntimeError('push failed')", dead_letter.error)

    async def test_failed_broadcast_push_is_dead_lettered(self):
        channel, dead_letters = channel_with_dead_letters()
        broken = register_broken_queue(channel)
        healthy = channel.add_listener()
        healthy.start()

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(healthy.id).type)
        self.assertEqual(broken.id, dead_letters.queue.pop().listener_id)
        with self.assertRaises(NoMessagesException):
            dead_letters.queue.pop()

    async def test_failed_on_message_is_dead_lettered(self):
        channel, dead_letters = channel_with_dead_letters()
        listener = BrokenListener()
        channel.register_listener(listener)
        listener.start()

        channel.dispatch(listener.id, Message(msg_type='first'))
        channel.dispatch(listener.id, Message(msg_type='second'))
        channel.deliver_next(listener.id)
        await channel.wait_next(listener.id, timeout=0.01)

        first, second = dead_letters.queue.pop(), dead_letters.queue.pop()
        self.assertEqual(('first', listener.id), (first.type, first.listener_id))
        self.assertEqual(('second', listener.id), (second.type, second.listener_id))
        self.assertEqual("RuntimeError('on_message failed')", first.error)

    async def test_pop_errors_are_not_dead_lettered(self):
        channel, dead_letters = channel_with_dead_letters()
        listener = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.deliver_next(listener.id)

        with self.assertRaises(NoMessagesException):
            dead_letters.queue.pop()

    async def test_custom_queue(self):
        queue = InMemoryQueue()
        channel, dead_letters = channel_with_dead_letters(DeadLetterHandler(queue))
        listener = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, Message(msg_type='test'))

        self.assertIs(queue, dead_letters.queue)
        self.assertEqual('test', queue.pop().type)

    async def test_broken_dead_letter_queue_keeps_original_error(self):
        channel, _ = channel_with_dead_letters(DeadLetterHandler(BrokenQueue()))
        listener = register_broken_queue(channel)

        with patch('eric_sse.queue_patterns.logger') as logger:
            with self.assertRaises(RuntimeError) as raised:
                channel.dispatch(listener.id, Message(msg_type='test'))

        self.assertEqual('push failed', str(raised.exception))
        logger.error.assert_called_once()

    async def test_broken_dead_letter_queue_still_delivers_on_message_failure(self):
        channel, _ = channel_with_dead_letters(DeadLetterHandler(BrokenQueue()))
        listener = BrokenListener()
        channel.register_listener(listener)
        listener.start()
        channel.dispatch(listener.id, Message(msg_type='test'))

        with patch('eric_sse.queue_patterns.logger'):
            self.assertEqual('test', channel.deliver_next(listener.id).type)

    async def test_builder_registers_dead_letters_on_created_channels(self):
        dead_letters = DeadLetterHandler()
        channels = (
            ChannelRepositoryBuilder(SSEChannel)
            .queuing_error_handler(dead_letters)
            .listener_error_handler(dead_letters)
            .build()
        )
        channel = channels.create({})
        listener = BrokenListener()
        channel.register_listener(listener)
        listener.start()
        channel.dispatch(listener.id, Message(msg_type='test'))

        channel.deliver_next(listener.id)

        self.assertEqual('test', dead_letters.queue.pop().type)

    async def test_original_message_is_kept(self):
        channel, dead_letters = channel_with_dead_letters()
        listener = register_broken_queue(channel)
        original = SignedMessage(sender_id='producer', msg_type='test', msg_id='m1')

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, original)

        dead_letter = dead_letters.queue.pop()
        self.assertIs(original, dead_letter.message)
        self.assertEqual('m1', dead_letter.id)

    async def test_redelivery(self):
        channel, dead_letters = channel_with_dead_letters()
        listener = BrokenListener()
        channel.register_listener(listener)
        listener.start()
        channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hello'))
        channel.deliver_next(listener.id)

        dead_letter = dead_letters.queue.pop()
        channel.dispatch(dead_letter.listener_id, dead_letter.message)

        redelivered = channel.deliver_next(listener.id)
        self.assertEqual(('test', 'hello'), (redelivered.type, redelivered.payload))


class ReliableQueueTestCase(IsolatedAsyncioTestCase):

    def test_pop_wraps_and_keeps_message_in_flight(self):
        queue = ReliableQueue()
        original = Message(msg_type='test', msg_payload='hello')
        queue.push(original)

        msg = queue.pop()

        self.assertIsInstance(msg, ReliableMessage)
        self.assertIs(original, msg.message)
        self.assertEqual(('test', 'hello', 1), (msg.type, msg.payload, msg.deliveries))
        self.assertEqual([msg.id], [m.id for m in queue.in_flight()])
        with self.assertRaises(NoMessagesException):
            queue.pop()

    def test_ack_removes_for_good(self):
        queue = ReliableQueue(visibility_timeout=0)
        queue.push(Message(msg_type='test'))
        msg = queue.pop()

        self.assertTrue(queue.ack(msg.id))
        self.assertFalse(queue.ack(msg.id))
        self.assertEqual([], queue.in_flight())
        self.assertEqual(0, queue.requeue_expired())
        with self.assertRaises(NoMessagesException):
            queue.pop()

    def test_nack_requeues_at_the_end(self):
        queue = ReliableQueue()
        queue.push(Message(msg_type='first'))
        queue.push(Message(msg_type='second'))
        first = queue.pop()

        self.assertTrue(queue.nack(first.id))
        self.assertFalse(queue.nack(first.id))

        self.assertEqual('second', queue.pop().type)
        redelivered = queue.pop()
        self.assertEqual((first.id, 'first', 2), (redelivered.id, redelivered.type, redelivered.deliveries))

    def test_unknown_id(self):
        queue = ReliableQueue()
        self.assertFalse(queue.ack('nope'))
        self.assertFalse(queue.nack('nope'))

    def test_expired_messages_are_requeued_on_pop(self):
        queue = ReliableQueue(visibility_timeout=0.01)
        queue.push(Message(msg_type='test'))
        msg = queue.pop()

        time.sleep(0.02)

        redelivered = queue.pop()
        self.assertEqual((msg.id, 2), (redelivered.id, redelivered.deliveries))

    def test_late_ack_after_requeue(self):
        queue = ReliableQueue(visibility_timeout=0.01)
        queue.push(Message(msg_type='test'))
        msg = queue.pop()
        time.sleep(0.02)

        self.assertEqual(1, queue.requeue_expired())
        self.assertFalse(queue.ack(msg.id))
        self.assertEqual(msg.id, queue.pop().id)

    def test_not_expired_messages_stay_in_flight(self):
        queue = ReliableQueue(visibility_timeout=60)
        queue.push(Message(msg_type='test'))
        queue.pop()

        self.assertEqual(0, queue.requeue_expired())
        self.assertEqual(1, len(queue.in_flight()))

    def test_no_visibility_timeout(self):
        queue = ReliableQueue(visibility_timeout=None)
        queue.push(Message(msg_type='test'))
        msg = queue.pop()

        self.assertEqual(0, queue.requeue_expired())
        self.assertTrue(queue.nack(msg.id))
        self.assertEqual(msg.id, queue.pop().id)

    async def test_wait_pop(self):
        queue = ReliableQueue()
        waiting = asyncio.create_task(queue.wait_pop(1))
        await asyncio.sleep(0)
        queue.push(Message(msg_type='test'))

        msg = await waiting

        self.assertEqual(('test', 1), (msg.type, msg.deliveries))
        self.assertEqual([msg.id], [m.id for m in queue.in_flight()])

    async def test_wait_pop_requeues_expired(self):
        queue = ReliableQueue(visibility_timeout=0.01)
        queue.push(Message(msg_type='test'))
        msg = await queue.wait_pop(1)
        await asyncio.sleep(0.02)

        self.assertEqual(msg.id, (await queue.wait_pop(1)).id)

    def test_custom_queue_and_in_flight_storage(self):
        inner, in_flight = InMemoryQueue(), InMemoryStorage()
        queue = ReliableQueue(inner, in_flight=in_flight)
        queue.push(Message(msg_type='test'))

        self.assertIsInstance(inner.pop(), ReliableMessage)
        queue.push(Message(msg_type='test'))
        msg = queue.pop()
        self.assertEqual([msg.id], list(in_flight.items.keys()))

    def test_pickle(self):
        queue = ReliableQueue(PicklableQueue())
        queue.push(Message(msg_type='first'))
        queue.push(Message(msg_type='second'))
        popped = queue.pop()

        restored = pickle.loads(pickle.dumps(queue))

        self.assertTrue(restored.ack(popped.id))
        self.assertEqual('second', restored.pop().type)

    async def test_channel_delivers_reliable_messages(self):
        channel = FakeChannel()
        queue = ReliableQueue()
        listener = MessageQueueListener()
        channel.register_connection(Connection(listener=listener, queue=queue))
        listener.start()
        channel.dispatch(listener.id, Message(msg_type='test'))

        msg = channel.deliver_next(listener.id)

        self.assertIsInstance(msg, ReliableMessage)
        self.assertTrue(queue.ack(msg.id))


class PicklableQueue(Queue):
    def __init__(self):
        self.items = []

    def pop(self, timeout: float = 0) -> MessageContract:
        if not self.items:
            raise NoMessagesException
        return self.items.pop(0)

    def push(self, message: MessageContract) -> None:
        self.items.append(message)
