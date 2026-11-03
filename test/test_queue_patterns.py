from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import NoMessagesException
from eric_sse.message import Message, UniqueMessage
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import DeadLetter, DeadLetterHandler
from eric_sse.queues import InMemoryQueue
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
        original = UniqueMessage(Message(msg_type='test'), sender_id='producer')

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, original)

        self.assertIs(original, dead_letters.queue.pop().message)

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
