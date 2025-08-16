from unittest import TestCase

import pytest

import eric_sse.exception
from eric_sse.queues import InMemoryQueue
from eric_sse.serializable import ChannelRepository, ListenerRepository, QueueRepository, ConnectionRepository
from eric_sse.prefabs import SSEChannel
from eric_sse.inmemory import InMemoryStorage
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message

class TestChannelRepository(TestCase):

    def test_repositories(self):
        sut = ChannelRepository(
            storage_engine=InMemoryStorage(),
            connection_repository=ConnectionRepository(
                storage_engine=InMemoryStorage(),
                listeners_repository=ListenerRepository(InMemoryStorage()),
                queues_repository=QueueRepository(InMemoryStorage()),
            )
        )


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

    def test_full_flow(self):

        sse_channel = SSEChannel(stream_delay_seconds=20)
        listener = MessageQueueListener()
        queue = InMemoryQueue()
        sse_channel.register_connection(listener=listener, queue=queue)
        sse_channel.dispatch(listener_id=listener.id, msg=Message(msg_type='test'))

        sut = ChannelRepository(
            storage_engine=InMemoryStorage(),
            connection_repository=ConnectionRepository(
                storage_engine=InMemoryStorage(),
                listeners_repository=ListenerRepository(InMemoryStorage()),
                queues_repository=QueueRepository(InMemoryStorage()),
            )
        )

        sut.persist(sse_channel)
        channel_loaded = sut.load_one(sse_channel.kv_key)

        listener_loaded = sse_channel.get_listener(listener.id)
        listener_loaded.start()

        try:
            msg = channel_loaded.deliver_next(listener_id=listener.id)
            self.assertEqual(msg.type, 'test')
        except eric_sse.exception.NoMessagesException:
            self.fail(f'Unexpected exception was raised')




