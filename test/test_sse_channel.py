from unittest import IsolatedAsyncioTestCase, TestCase

from eric_sse.prefabs import SSEChannel
from eric_sse.entities import Message
from eric_sse.inmemory import InMemoryChannelRepository


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



    def test_parameters_are_maintained(self):
        sut = SSEChannel(
            stream_delay_seconds=3,
            retry_timeout_milliseconds=27,
            channel_id='test',
        )
        constructor_params = sut.kv_constructor_params_as_dict
        self.assertEqual(3, constructor_params['stream_delay_seconds'])
        self.assertEqual(27, constructor_params['retry_timeout_milliseconds'])
        self.assertEqual('test', constructor_params['channel_id'])

class SSEChannelInMemoryPersistenceTestCase(TestCase):

    def setUp(self):
        self.sut = InMemoryChannelRepository()

    def test_crud(self):
        repo = self.sut
        channel = SSEChannel()
        repo.persist(channel)
        self.assertEqual(1, len([x for x in repo.load_all()]))
        channel_loaded = repo.load_one(channel_id=channel.id)
        self.assertEqual(channel.id, channel_loaded.id)
