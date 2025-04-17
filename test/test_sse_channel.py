import json

from unittest import IsolatedAsyncioTestCase
from eric_sse.prefabs import SSEChannel
from eric_sse.entities import MessageQueueListener, Message
from eric_sse.exception import NoMessagesException

from test.mock.listener import MessageQueueListenerMock


class SSEStreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = SSEChannel()
        SSEChannel.NEXT_ID = 1
        MessageQueueListener.NEXT_ID = 1

    async def test_broadcast_interaction_with_listeners(self):

        # scenario is: 1 channel and 2 listeners
        channel = self.sut
        listener1 = MessageQueueListenerMock()
        listener2 = MessageQueueListenerMock()
        channel.register_listener(listener1)
        channel.register_listener(listener2)

        listener1.start_sync()
        listener2.start_sync()

        # 1 broadcast
        msg_to_send = Message(msg_type='test', msg_payload={})
        channel.broadcast(msg=msg_to_send)

        # message is received correctly
        async for msg_received in await self.sut.message_stream(listener=listener1):
            self.assertDictEqual(
                {'data': {}, 'event': 'test', 'retry': channel.retry_timeout_milliseconds}, msg_received
            )

        # and it has been the only one
        self.assertEqual(1, listener1.num_received)

        with self.assertRaises(NoMessagesException):
            self.sut.deliver_next(listener1.id)

        self.assertEqual(msg_to_send, self.sut.deliver_next(listener2.id))

        with self.assertRaises(NoMessagesException):
            self.sut.deliver_next(listener2.id)

    async def test_payload_adapter_json(self):
        self.sut.payload_adapter = json.dumps
        listener = MessageQueueListenerMock()
        self.sut.register_listener(listener)
        listener.start_sync()
        self.sut.dispatch(listener.id, Message(msg_type="test", msg_payload={'a': 1}))

        async for m in await self.sut.message_stream(listener):
            self.assertEqual(m['data'], json.dumps({'a': 1}))

        self.assertEqual(1, listener.num_received)

    async def test_dispatch_sse_payload(self):
        c = self.sut
        listener = MessageQueueListenerMock(num_messages_before_disconnect=1)
        c.register_listener(listener)
        await listener.start()
        c.dispatch(listener.id, Message(msg_type='test', msg_payload={'a': 1}))

        async for msg in await c.message_stream(listener):
            self.assertDictEqual({'data': {'a': 1}, 'event': 'test', 'retry': c.retry_timeout_milliseconds}, msg)

        self.assertEqual(1, listener.num_received)


    async def test_stream_stops_if_listener_stops(self):
        l = self.sut.add_listener()
        self.sut.dispatch(l.id, Message(msg_type='test'))
        self.sut.dispatch(l.id, Message(msg_type='test'))

        await l.start()
        async for m in await self.sut.message_stream(listener=l):
            self.assertEqual('test', m['event'])
            await l.stop()

        await l.start()
        async for m in await self.sut.message_stream(listener=l):
            self.assertEqual('test', m['event'])
            await l.stop()