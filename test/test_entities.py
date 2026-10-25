from unittest import IsolatedAsyncioTestCase, TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.prefabs import DataProcessingChannel, SSEChannel
from eric_sse.contracts.channel import ChannelContract


class SSEChannelTestCase(ChannelContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel)

    def channel_data(self) -> dict:
        return {'retry_timeout_milliseconds': 10}


class DataProcessingChannelTestCase(ChannelContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(DataProcessingChannel)

    def channel_data(self) -> dict:
        return {'max_workers': 2}


class ChannelWithoutRepositoryTestCase(TestCase):
    """No Builder here on purpose: the use case is a channel that works in memory on its own."""

    def test_connections_work_in_memory(self):
        channel = SSEChannel()
        added = channel.add_connection()
        listener = MessageQueueListener()
        registered = channel.register_listener(listener)
        added.listener.start()
        listener.start()

        channel.broadcast(Message(msg_type='test'))

        self.assertIs(listener, registered.listener)
        self.assertEqual('test', channel.deliver_next(added.id).type)
        self.assertEqual('test', channel.deliver_next(registered.id).type)
