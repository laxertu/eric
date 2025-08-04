from copyreg import constructor
from typing import Iterable
from unittest import IsolatedAsyncioTestCase
from eric_sse.persistence import PersistableConnection, importlib_create_instance
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


    def test_persistable_behavior(self):
        self.assertEqual('eric_sse.prefabs.SSEChannel', self.sut.kv_class_absolute_path)

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
        self.assertEqual('eric_sse.persistence.InMemoryConnectionRepository', channel.kv_value_as_dict['connections_repository'])

        self.sut = SSEChannel(connections_repository=ConnectionRepositoryFake())
        self.assertEqual('test.test_sse_channel.ConnectionRepositoryFake', self.sut.kv_value_as_dict['connections_repository'])

        sut_2 = importlib_create_instance(
            class_full_path=channel.kv_class_absolute_path,
            constructor_params=channel.kv_constructor_params_as_dict,
            setup_values=channel.kv_value_as_dict
        )
        self.assertIs(type(sut_2), SSEChannel)

    def test_parameters_are_maintained(self):
        sut = SSEChannel(
            stream_delay_seconds=3,
            retry_timeout_milliseconds=27,
            connections_repository=ConnectionRepositoryFake(),
            channel_id='test',
        )
        constructor_params = sut.kv_constructor_params_as_dict
        self.assertEqual(3, constructor_params['stream_delay_seconds'])
        self.assertEqual(27, constructor_params['retry_timeout_milliseconds'])
        self.assertEqual('test', constructor_params['channel_id'])
