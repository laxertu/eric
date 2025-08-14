from unittest import TestCase

from eric_sse.queues import InMemoryQueue
from eric_sse.serializable import ChannelRepository, ListenerRepository, QueueRepository
from eric_sse.prefabs import SSEChannel
from eric_sse.inmemory import InMemoryStorage
from eric_sse.listener import MessageQueueListener


class TestChannelRepository(TestCase):

    def test_repositories(self):
        sut = ChannelRepository(InMemoryStorage())
        channel = SSEChannel(stream_delay_seconds=20)
        sut.persist(channel)

        channel_loaded = sut.load_one(channel.kv_key)
        self.assertTrue(channel_loaded is channel)

        sut2 = ListenerRepository(InMemoryStorage())
        listener = MessageQueueListener()
        sut2.persist(listener)
        listener_clone = sut2.load(listener.id)
        self.assertTrue(listener_clone is listener)

        sut3 = QueueRepository(InMemoryStorage())
        queue = InMemoryQueue()

        sut3.persist(queue)
        queue_clone = sut3.load(queue.id)
        self.assertTrue(queue_clone is queue)


