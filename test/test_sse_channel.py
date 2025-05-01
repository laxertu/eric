import json

from unittest import IsolatedAsyncioTestCase
from eric_sse.prefabs import SSEChannel
from eric_sse.entities import MessageQueueListener, Message
from test.mock.listener import MessageQueueListenerMock


class SSEStreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = SSEChannel()
        SSEChannel.NEXT_ID = 1
        MessageQueueListener.NEXT_ID = 1

    async def test_sse_channel_default_output(self):
        # setup
        channel = self.sut
        listener = channel.add_listener()
        await listener.start()

        msg_to_send = Message(msg_type='test', msg_payload={})
        channel.dispatch(listener_id=listener.id, msg=msg_to_send)

        async for msg_received in await self.sut.message_stream(listener=listener):
            self.assertDictEqual(
                {'data': {}, 'event': 'test', 'retry': channel.retry_timeout_milliseconds}, msg_received
            )
            await listener.stop()


    async def test_payload_adapter_json(self):
        self.sut.payload_adapter = json.dumps
        listener = MessageQueueListenerMock(num_messages_before_disconnect=1)
        self.sut.register_listener(listener)
        listener.start_sync()
        self.sut.dispatch(listener.id, Message(msg_type="test", msg_payload={'a': 1}))

        async for m in await self.sut.message_stream(listener):
            self.assertEqual(m['data'], json.dumps({'a': 1}))


    async def test_stream_stops_if_listener_stops(self):
        l = self.sut.add_listener()
        self.sut.dispatch(l.id, Message(msg_type='test'))
        self.sut.dispatch(l.id, Message(msg_type='test'))

        l.start_sync()
        total_messages_received = 0
        async for _ in await self.sut.message_stream(listener=l):
            total_messages_received += 1
            await l.stop()

        await l.start()
        async for _ in await self.sut.message_stream(listener=l):
            total_messages_received += 1
            await l.stop()

        self.assertEqual(2, total_messages_received)