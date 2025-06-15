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
        """
        Tests that the SSEChannel produces the correct default output for a dispatched message.
        
        Verifies that a listener receives a message with the expected structure and values when a message is dispatched, and that the listener can be stopped after receiving the message.
        """
        channel = self.sut
        listener = channel.add_listener()
        await listener.start()

        msg_to_send = Message(msg_type='test', msg_payload={})
        channel.dispatch(listener_id=listener.id, msg=msg_to_send)

        async for msg_received in self.sut.message_stream(listener=listener):
            self.assertDictEqual(
                {'data': {}, 'event': 'test', 'retry': channel.retry_timeout_milliseconds}, msg_received
            )
            await listener.stop()


    async def test_payload_adapter_json(self):
        """
        Tests that the SSEChannel correctly uses a custom payload adapter for message serialization.
        
        Verifies that when the payload_adapter is set to json.dumps, the 'data' field of streamed messages contains the JSON-serialized payload.
        """
        self.sut.payload_adapter = json.dumps
        listener = MessageQueueListenerMock(num_messages_before_disconnect=1)
        self.sut.register_listener(listener)
        listener.start_sync()
        self.sut.dispatch(listener.id, Message(msg_type="test", msg_payload={'a': 1}))

        async for m in self.sut.message_stream(listener):
            self.assertEqual(m['data'], json.dumps({'a': 1}))


    async def test_stream_stops_if_listener_stops(self):
        """
        Tests that the message stream stops when the listener is stopped and resumes correctly.
        
        Verifies that messages are received only while the listener is active, and that stopping and restarting the listener results in the correct total number of messages received.
        """
        l = self.sut.add_listener()
        self.sut.dispatch(l.id, Message(msg_type='test'))
        self.sut.dispatch(l.id, Message(msg_type='test'))

        l.start_sync()
        total_messages_received = 0
        async for _ in self.sut.message_stream(listener=l):
            total_messages_received += 1
            await l.stop()

        await l.start()
        async for _ in self.sut.message_stream(listener=l):
            total_messages_received += 1
            await l.stop()

        self.assertEqual(2, total_messages_received)