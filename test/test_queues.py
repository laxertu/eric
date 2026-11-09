import asyncio
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import ReliableQueue
from eric_sse.queues import InMemoryQueue, Queue
from test.queue_contract import QueueContract


class SyncOnlyQueue(Queue):
    """A queue implementing only the abstract methods, like a third party backend."""
    def __init__(self):
        self.inner = InMemoryQueue()

    def pop(self, timeout: float = 0) -> MessageContract:
        return self.inner.pop(timeout)

    def push(self, message: MessageContract) -> None:
        self.inner.push(message)


class InMemoryQueueTestCase(QueueContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel).queues(InMemoryQueue)

    def channel_data(self) -> dict:
        return {}


class SyncOnlyQueueTestCase(QueueContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel).queues(SyncOnlyQueue)

    def channel_data(self) -> dict:
        return {}


class ReliableQueueAsPlainQueueTestCase(QueueContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel).queues(ReliableQueue)

    def channel_data(self) -> dict:
        return {}


class InMemoryQueueWakeUpRaceTestCase(IsolatedAsyncioTestCase):

    async def test_message_arrived_when_the_wait_times_out_is_delivered(self):
        # White box on purpose: this state, a message queued whose wake-up hasn't run yet when the timeout fires,
        # can't be produced deterministically through the public API.
        channel = ChannelRepositoryBuilder(SSEChannel).build().create({})
        connection = channel.add_connection()
        connection.listener.start()
        pending_push = connection.queue._InMemoryQueue__queue
        asyncio.get_running_loop().call_later(0.01, pending_push.put, Message(msg_type='late'))

        self.assertEqual('late', (await channel.wait_next(connection.id, 0.05)).type)
