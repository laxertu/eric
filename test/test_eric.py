import json
from unittest import TestCase, IsolatedAsyncioTestCase

from eric_sse.entities import Message, MessageQueueListener, SignedMessage
from eric_sse.prefabs import SSEChannel, SimpleDistributedApplicationListener, DataProcessingChannel


class MessageQueueListenerMock(MessageQueueListener):

    def __init__(self, num_messages_before_disconnect=1, fixtures: dict[int, Message] = None):
        super().__init__()
        self.disconnect_after = num_messages_before_disconnect
        self.num_received = 0
        self.fixtures = fixtures

    def on_message(self, msg: Message) -> None:
        self.num_received += 1

        if self.fixtures is not None:
            assert msg.type == self.fixtures[self.num_received].type
            assert msg.payload == self.fixtures[self.num_received].payload

        if self.num_received >= self.disconnect_after:
            self.stop_sync()


class ListenerTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = MessageQueueListener()

    async def test_start_stop(self):
        self.assertFalse(await self.sut.is_running())

        await self.sut.start()
        self.assertTrue(await self.sut.is_running())

        await self.sut.stop()
        self.assertFalse(await self.sut.is_running())

        await self.sut.start()
        self.assertTrue(await self.sut.is_running())


class SSEChannelTestCase(TestCase):

    def setUp(self):
        self.sut = SSEChannel()
        MessageQueueListener.NEXT_ID = 1

    def test_listeners_ids_generation(self):
        l_1 = MessageQueueListenerMock()
        self.assertEqual('1', l_1.id)

        l_2 = MessageQueueListenerMock()
        self.assertEqual('2', l_2.id)

        l_3 = MessageQueueListenerMock()
        self.assertEqual('3', l_3.id)


class SSEStreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = SSEChannel()
        SSEChannel.NEXT_ID = 1
        MessageQueueListener.NEXT_ID = 1

    async def test_broadcast_ok(self):

        # scenario is: 1 channel and 2 listeners
        c = self.sut
        m_1 = MessageQueueListenerMock()
        m_2 = MessageQueueListenerMock()
        c.register_listener(m_1)
        c.register_listener(m_2)

        m_1.start_sync()
        m_2.start_sync()

        # 1 broadcast
        msg_to_send = Message(type='test', payload={})
        c.broadcast(msg=msg_to_send)
        expected = {
            m_1.id: [msg_to_send],
            m_2.id: [msg_to_send]
        }
        self.assertEqual(expected, c.queues)

        # message is received correctly
        async for msg_received in await self.sut.message_stream(listener=m_1):
            self.assertDictEqual(
                {'data': {}, 'event': 'test', 'retry': c.retry_timeout_milliseconds}, msg_received
            )
        self.assertEqual(1, m_1.num_received)
        # queue is ok
        expected = {
            m_1.id: [],
            m_2.id: [msg_to_send]
        }
        self.assertEqual(expected, c.queues)

    async def test_payload_adapter_json(self):
        self.sut.payload_adapter = json.dumps
        listener = MessageQueueListenerMock()
        self.sut.register_listener(listener)
        listener.start_sync()
        self.sut.dispatch(listener.id, Message(type="test", payload={'a': 1}))

        async for m in await self.sut.message_stream(listener):
            self.assertEqual(m['data'], json.dumps({'a': 1}))

        self.assertEqual(1, listener.num_received)

    async def test_dispatch_ok(self):
        c = self.sut
        listener = MessageQueueListenerMock(num_messages_before_disconnect=2)
        c.register_listener(listener)
        await listener.start()
        c.dispatch(listener.id, Message(type='test', payload={'a': 1}))
        c.dispatch(listener.id, Message(type='test', payload={'a': 1}))

        async for msg in await c.message_stream(listener):
            self.assertDictEqual({'data': {'a': 1}, 'event': 'test', 'retry': c.retry_timeout_milliseconds}, msg)

        self.assertDictEqual({listener.id: []}, c.queues)
        self.assertEqual(2, listener.num_received)

    async def test_listener_as_consumer(self):
        c = self.sut
        msg1 = Message('test', {'a': 1})
        msg2 = Message('test', {'b': 2})

        listener = MessageQueueListenerMock(
            num_messages_before_disconnect=2, fixtures={1: msg1, 2: msg2}
        )
        c.register_listener(listener)

        c.dispatch(listener.id, msg1)
        c.dispatch(listener.id, msg2)

        await listener.start()

        async for _ in await self.sut.message_stream(listener=listener):
            pass

    async def test_listener_start_stop(self):
        l = self.sut.add_listener()
        self.sut.dispatch(l.id, Message(type='test'))
        self.sut.dispatch(l.id, Message(type='test'))

        await l.start()
        async for m in await self.sut.message_stream(listener=l):
            self.assertEqual('test', m['event'])
            await l.stop()

        await l.start()
        async for m in await self.sut.message_stream(listener=l):
            self.assertEqual('test', m['event'])
            await l.stop()



class SignedMessageTestCase(TestCase):

    def test_signed_message(self):
        sut = SignedMessage(sender_id='1', msg_type='test', msg_payload='hi')
        self.assertEqual(sut.payload, {'sender_id': '1', 'payload': 'hi'})
        self.assertEqual(sut.sender_id, '1')



def hello_response(m: Message) -> list[Message]:
    return [
        Message(type='hello_ack', payload=f'{m.payload["payload"]}!'),
        Message(type='stop')
    ]

def hello_ack_response(m: Message) -> list[Message]:
    return [
        Message(type='stop')
    ]


class DistributedListenerTestCase(IsolatedAsyncioTestCase):

    @staticmethod
    def create_listener(ch: SSEChannel):
        l = SimpleDistributedApplicationListener(ch)
        l.set_action('hello', hello_response)
        l.set_action('hello_ack', hello_ack_response)
        l.start_sync()
        return l


    async def test_application(self):
        ssc = SSEChannel()

        alice = DistributedListenerTestCase.create_listener(ssc)
        bob = DistributedListenerTestCase.create_listener(ssc)

        # Bob says hello to Alice
        bob.dispatch_to(alice, Message(type='hello', payload='hello!'))

        # Alice will stop after having answered to Bob
        bob.dispatch_to(alice, Message(type='stop'))

        types = [m['event'] async for m in await ssc.message_stream(alice)]
        self.assertEqual(['hello', 'stop'], types)

        types = [m['event'] async for m in await ssc.message_stream(bob)]
        self.assertEqual(['hello_ack', 'stop'], types)

class DataProcessingChannelTestCase(IsolatedAsyncioTestCase):
    async def test_channel(self):
        channel = DataProcessingChannel(stream_delay_seconds=0, max_workers=2)
        listener = MessageQueueListenerMock()
        channel.register_listener(listener)

        channel.dispatch(listener.id, Message(type='test1'))
        channel.dispatch(listener.id, Message(type='test2'))
        channel.dispatch(listener.id, Message(type='test3'))

        await listener.start()
        types = {m['event'] async for m in await channel.process_queue(listener)}
        self.assertEqual({'test1', 'test2', 'test3'}, types)
