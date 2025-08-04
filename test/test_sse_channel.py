from typing import Iterable
from unittest import IsolatedAsyncioTestCase

from eric_sse.persistence import PersistableConnection
from eric_sse.prefabs import SSEChannel
from eric_sse.entities import Message, ConnectionRepositoryInterface
from eric_sse.queues import Queue


class ConnectionRepositoryFake(ConnectionRepositoryInterface):

    def create_queue(self, listener_id: str) -> Queue:
        pass

    def persist(self, channel_id: str, connection: PersistableConnection) -> None:
        pass

    def load_all(self) -> Iterable[PersistableConnection]:
        pass

    def load(self, channel_id: str) -> Iterable[PersistableConnection]:
        pass

    def delete(self, channel_id: str, listener_id: str) -> None:
        pass


class SSEStreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = SSEChannel()


    async def test_sse_channel_default_output(self):
        # setup
        channel = self.sut
        listener = channel.add_listener()
        listener.start()

        msg_to_send = Message(msg_type='test', msg_payload={})
        channel.dispatch(listener_id=listener.id, msg=msg_to_send)

        async for msg_received in self.sut.message_stream(listener=listener):
            self.assertDictEqual(
                {'data': {}, 'event': 'test', 'retry': channel.retry_timeout_milliseconds}, msg_received
            )
            listener.stop()




    async def test_stream_stops_if_listener_stops(self):
        l = self.sut.add_listener()
        self.sut.dispatch(l.id, Message(msg_type='test'))
        self.sut.dispatch(l.id, Message(msg_type='test'))

        l.start()
        total_messages_received = 0
        async for _ in self.sut.message_stream(listener=l):
            total_messages_received += 1
            l.stop()

        l.start()
        async for _ in self.sut.message_stream(listener=l):
            total_messages_received += 1
            l.stop()

        self.assertEqual(2, total_messages_received)


    async def test_sse_channel_persistence(self):
        channel = self.sut
        self.assertEqual('InMemoryConnectionRepository', channel.kv_value_as_dict['connections_repository'])

        self.sut = SSEChannel(connections_repository=ConnectionRepositoryFake())
        self.assertEqual('ConnectionRepositoryFake', self.sut.kv_value_as_dict['connections_repository'])
