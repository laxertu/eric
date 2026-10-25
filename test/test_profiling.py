import pickle
import time
from unittest import IsolatedAsyncioTestCase, TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.exception import NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.profiling import CallStats, ProfiledListener, ProfiledQueue
from eric_sse.queues import InMemoryQueue
from test.mock.channel import FakeChannel
from eric_sse.contracts.doubles import BrokenListener
from test.test_queue_patterns import PicklableQueue


class SlowQueue(InMemoryQueue):
    def push(self, message: MessageContract) -> None:
        time.sleep(0.01)
        super().push(message)


class RecordingListener(MessageQueueListener):
    def __init__(self):
        super().__init__()
        self.received = []
        self.channels = []

    def on_message(self, msg: MessageContract) -> None:
        self.received.append(msg.type)

    def on_registered(self, channel, connection_id) -> None:
        self.channels.append(channel)


class CallStatsTestCase(TestCase):

    def test_record(self):
        stats = CallStats()
        self.assertEqual((0, 0.0, 0.0), (stats.calls, stats.total_time, stats.mean_time))

        stats.record(1.0)
        stats.record(3.0)

        self.assertEqual((2, 4.0, 2.0), (stats.calls, stats.total_time, stats.mean_time))


class ProfiledQueueTestCase(IsolatedAsyncioTestCase):

    def test_push_and_pop_are_delegated_and_counted(self):
        inner = InMemoryQueue()
        queue = ProfiledQueue(inner)

        queue.push(Message(msg_type='first'))
        queue.push(Message(msg_type='second'))
        self.assertEqual('first', inner.pop().type)
        self.assertEqual('second', queue.pop().type)

        self.assertIs(inner, queue.queue)
        self.assertEqual(2, queue.push_stats.calls)
        self.assertEqual(1, queue.pop_stats.calls)
        self.assertEqual(0, queue.wait_pop_stats.calls)

    def test_empty_pop_is_counted_and_raises(self):
        queue = ProfiledQueue(InMemoryQueue())

        with self.assertRaises(NoMessagesException):
            queue.pop()

        self.assertEqual(1, queue.pop_stats.calls)

    def test_time_is_measured(self):
        queue = ProfiledQueue(SlowQueue())

        queue.push(Message(msg_type='test'))
        queue.push(Message(msg_type='test'))

        self.assertGreaterEqual(queue.push_stats.total_time, 0.02)
        self.assertGreaterEqual(queue.push_stats.mean_time, 0.01)

    async def test_wait_pop_includes_waiting(self):
        queue = ProfiledQueue(InMemoryQueue())

        with self.assertRaises(NoMessagesException):
            await queue.wait_pop(0.02)
        queue.push(Message(msg_type='test'))
        self.assertEqual('test', (await queue.wait_pop(1)).type)

        self.assertEqual(2, queue.wait_pop_stats.calls)
        self.assertGreaterEqual(queue.wait_pop_stats.total_time, 0.02)

    def test_pickle(self):
        queue = ProfiledQueue(PicklableQueue())
        queue.push(Message(msg_type='test'))

        restored = pickle.loads(pickle.dumps(queue))

        self.assertEqual('test', restored.pop().type)
        self.assertEqual((1, 1), (restored.push_stats.calls, restored.pop_stats.calls))


class ProfiledListenerTestCase(IsolatedAsyncioTestCase):

    def test_delegates_and_counts(self):
        inner = RecordingListener()
        listener = ProfiledListener(inner)

        listener.on_message(Message(msg_type='test'))
        listener.start()

        self.assertIs(inner, listener.listener)
        self.assertEqual(['test'], inner.received)
        self.assertTrue(inner.is_running())
        self.assertTrue(listener.is_running())
        listener.stop()
        self.assertFalse(inner.is_running())
        self.assertEqual(1, listener.on_message_stats.calls)

    def test_failing_on_message_is_counted_and_raises(self):
        listener = ProfiledListener(BrokenListener())

        with self.assertRaises(RuntimeError):
            listener.on_message(Message(msg_type='test'))

        self.assertEqual(1, listener.on_message_stats.calls)


class ProfiledChannelTestCase(IsolatedAsyncioTestCase):

    async def test_profiled_connection(self):
        channel = FakeChannel()
        inner = RecordingListener()
        listener = ProfiledListener(inner)
        queue = ProfiledQueue(InMemoryQueue())
        connection = Connection(listener=listener, queue=queue)
        channel.register_connection(connection)
        listener.start()

        for i in range(10):
            channel.dispatch(connection.id, Message(msg_type=str(i)))
        for _ in range(5):
            channel.deliver_next(connection.id)
        for _ in range(5):
            await channel.wait_next(connection.id, timeout=1)

        self.assertEqual([channel], inner.channels)
        self.assertEqual([str(i) for i in range(10)], inner.received)
        self.assertEqual((10, 5, 5), (queue.push_stats.calls, queue.pop_stats.calls, queue.wait_pop_stats.calls))
        self.assertEqual(10, listener.on_message_stats.calls)


class ProfiledBuilderTestCase(IsolatedAsyncioTestCase):

    async def test_every_connection_created_by_a_repository_is_profiled(self):
        repository = (
            ChannelRepositoryBuilder(FakeChannel)
            .listeners(lambda: ProfiledListener(RecordingListener()))
            .queues(lambda: ProfiledQueue(InMemoryQueue()))
            .build()
        )
        channel = repository.create({})
        connections = [channel.add_connection(), channel.add_connection()]

        for connection in connections:
            connection.listener.start()
        channel.broadcast(Message(msg_type='test'))
        for connection in connections:
            channel.deliver_next(connection.id)

        self.assertEqual([1, 1], [connection.listener.on_message_stats.calls for connection in connections])
