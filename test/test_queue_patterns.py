import pickle
import time
from typing import Any, Callable, Iterable
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.exception import ItemNotFound, NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract, SignedMessage
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import DeadLetterHandler, ReliableQueue
from eric_sse.queues import InMemoryQueue, Queue
from eric_sse.repository import ChannelRepository, InMemoryStorage, KvStorage
from test.reliable_queue_contract import ReliableQueueContract
from test.test_handlers import BrokenListener, BrokenQueue


def build_channels(
        dead_letters: DeadLetterHandler,
        listener_factory: Callable[[], MessageQueueListener] = MessageQueueListener,
        queue_factory: Callable[[], Queue] = InMemoryQueue
) -> ChannelRepository[SSEChannel]:
    return (
        ChannelRepositoryBuilder(SSEChannel)
        .listeners(listener_factory)
        .queues(queue_factory)
        .queuing_error_handler(dead_letters)
        .listener_error_handler(dead_letters)
        .build()
    )


def subscribe(channel: SSEChannel) -> MessageQueueListener:
    listener = channel.add_listener()
    listener.start()
    return listener


class DeadLetterHandlerTestCase(IsolatedAsyncioTestCase):

    def test_message_that_cannot_be_queued_is_dead_lettered_and_the_error_raised(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters, queue_factory=BrokenQueue).create({})
        listener = subscribe(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hello'))

        dead_letter = dead_letters.queue.pop()
        self.assertEqual(listener.id, dead_letter.listener_id)
        self.assertEqual(('test', 'hello'), (dead_letter.type, dead_letter.payload))
        self.assertEqual("RuntimeError('push failed')", dead_letter.error)

    def test_broadcast_dead_letters_only_messages_that_cannot_be_queued(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters).create({})
        healthy = subscribe(channel)
        broken = MessageQueueListener()
        channel.register_connection(Connection(listener=broken, queue=BrokenQueue()))

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(healthy.id).type)
        self.assertEqual(broken.id, dead_letters.queue.pop().listener_id)
        with self.assertRaises(NoMessagesException):
            dead_letters.queue.pop()

    async def test_messages_the_listener_fails_to_handle_are_dead_lettered(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters, listener_factory=BrokenListener).create({})
        listener = subscribe(channel)
        channel.dispatch(listener.id, Message(msg_type='first'))
        channel.dispatch(listener.id, Message(msg_type='second'))

        channel.deliver_next(listener.id)
        await channel.wait_next(listener.id, timeout=0.01)

        first, second = dead_letters.queue.pop(), dead_letters.queue.pop()
        self.assertEqual(('first', listener.id), (first.type, first.listener_id))
        self.assertEqual(('second', listener.id), (second.type, second.listener_id))
        self.assertEqual("RuntimeError('on_message failed')", first.error)

    def test_failed_reads_are_not_dead_lettered(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters, queue_factory=BrokenQueue).create({})
        listener = subscribe(channel)

        with self.assertRaises(RuntimeError):
            channel.deliver_next(listener.id)

        with self.assertRaises(NoMessagesException):
            dead_letters.queue.pop()

    def test_dead_letters_go_to_the_given_queue(self):
        queue = InMemoryQueue()
        channel = build_channels(DeadLetterHandler(queue), queue_factory=BrokenQueue).create({})
        listener = subscribe(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, Message(msg_type='test'))

        self.assertEqual('test', queue.pop().type)

    def test_lost_dead_letter_is_logged_and_the_original_error_raised(self):
        channel = build_channels(DeadLetterHandler(BrokenQueue()), queue_factory=BrokenQueue).create({})
        listener = subscribe(channel)

        with self.assertLogs(level='ERROR'):
            with self.assertRaises(RuntimeError) as raised:
                channel.dispatch(listener.id, Message(msg_type='test'))

        self.assertEqual('push failed', str(raised.exception))

    def test_lost_dead_letter_does_not_stop_delivery(self):
        channel = build_channels(DeadLetterHandler(BrokenQueue()), listener_factory=BrokenListener).create({})
        listener = subscribe(channel)
        channel.dispatch(listener.id, Message(msg_type='test'))

        with self.assertLogs(level='ERROR'):
            self.assertEqual('test', channel.deliver_next(listener.id).type)

    def test_channels_loaded_from_persistence_dead_letter_too(self):
        dead_letters = DeadLetterHandler()
        channels = build_channels(dead_letters, listener_factory=BrokenListener)
        channel = channels.create({})
        channels.persist(channel)
        loaded = channels.load_one(channel.id)
        listener = subscribe(loaded)
        loaded.dispatch(listener.id, Message(msg_type='test'))

        loaded.deliver_next(listener.id)

        self.assertEqual('test', dead_letters.queue.pop().type)

    def test_dead_letter_keeps_the_original_message(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters, queue_factory=BrokenQueue).create({})
        listener = subscribe(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(listener.id, SignedMessage(sender_id='producer', msg_type='test', msg_id='m1'))

        dead_letter = dead_letters.queue.pop()
        self.assertEqual('m1', dead_letter.id)
        self.assertEqual('producer', dead_letter.message.sender_id)

    def test_dead_letter_can_be_delivered_again(self):
        dead_letters = DeadLetterHandler()
        channel = build_channels(dead_letters, listener_factory=BrokenListener).create({})
        listener = subscribe(channel)
        channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hello'))
        channel.deliver_next(listener.id)

        dead_letter = dead_letters.queue.pop()
        channel.dispatch(dead_letter.listener_id, dead_letter.message)

        redelivered = channel.deliver_next(listener.id)
        self.assertEqual(('test', 'hello'), (redelivered.type, redelivered.payload))


class PicklingStorage(KvStorage):
    """Keeps values pickled, as an out-of-process storage would."""
    def __init__(self):
        self.items: dict[str, bytes] = {}

    def fetch_by_prefix(self, prefix: str) -> Iterable[Any]:
        return [pickle.loads(value) for key, value in list(self.items.items()) if key.startswith(prefix)]

    def upsert(self, key: str, value: Any):
        self.items[key] = pickle.dumps(value)

    def fetch_one(self, key: str) -> Any:
        try:
            return pickle.loads(self.items[key])
        except KeyError:
            raise ItemNotFound(key=key) from None

    def delete(self, key: str):
        self.items.pop(key, None)


class PicklableQueue(Queue):
    """Waits for messages by polling: no lock to drop when pickled."""
    def __init__(self):
        self.items = []

    def pop(self, timeout: float = 0) -> MessageContract:
        deadline = time.monotonic() + timeout
        while not self.items:
            if time.monotonic() >= deadline:
                raise NoMessagesException
            time.sleep(0.001)
        return self.items.pop(0)

    def push(self, message: MessageContract) -> None:
        self.items.append(message)


class DefaultReliableQueueTestCase(ReliableQueueContract, IsolatedAsyncioTestCase):
    def create_builder(self, visibility_timeout: float | None) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel).queues(lambda: ReliableQueue(visibility_timeout=visibility_timeout))

    def channel_data(self) -> dict:
        return {}


class PickledReliableQueueTestCase(ReliableQueueContract, IsolatedAsyncioTestCase):
    """Custom inner queue and in-flight storage, persisted pickled."""
    def create_builder(self, visibility_timeout: float | None) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel, PicklingStorage()).queues(
            lambda: ReliableQueue(PicklableQueue(), visibility_timeout=visibility_timeout, in_flight=InMemoryStorage())
        )

    def channel_data(self) -> dict:
        return {}
