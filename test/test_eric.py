from unittest import TestCase
from eric.model import Message, MessageQueueListener, SSEChannel
from unittest import IsolatedAsyncioTestCase

class DummyQueueListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        pass



class MessageQueueListenerMock(MessageQueueListener):

    def __init__(self, num_messages_before_disconnect=1, fixtures: dict[int, Message] = None):
        super().__init__()
        self.disconnect_after = num_messages_before_disconnect
        self.num_received = 0
        self.fixtures = fixtures

    async def is_running(self) -> bool:
        return self.num_received >= self.disconnect_after

    def on_message(self, msg: Message) -> None:
        self.num_received += 1
        if self.fixtures is not None:
            assert msg.type == self.fixtures[self.num_received].type
            assert msg.payload == self.fixtures[self.num_received].payload


class ListenerTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = DummyQueueListener()

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
        SSEChannel.NEXT_ID = 1
        MessageQueueListener.NEXT_ID = 1

    def test_listeners_ids_generation(self):
        l_1 = MessageQueueListenerMock()
        self.assertEqual('1', l_1.id)

        l_2 = MessageQueueListenerMock()
        self.assertEqual('2', l_2.id)

        l_3 = self.sut.add_listener(MessageQueueListenerMock)
        self.assertEqual('3', l_3.id)

    def test_broadcast_ok(self):

        # scenario is: 1 channel and 2 listeners
        c = self.sut
        l_1 = c.add_listener(MessageQueueListenerMock)
        l_2 = c.add_listener(MessageQueueListenerMock)

        # 1 broadcast
        msg_to_send = Message(type= 'test', payload={})
        c.broadcast(msg=msg_to_send)
        expected = {
            l_1.id: [msg_to_send],
            l_2.id: [msg_to_send]
        }
        self.assertEqual(expected, c.queues)

        # message is received correctly
        msg_received = c.deliver_next(listener_id=l_1.id)
        self.assertEqual(msg_to_send, msg_received)

        # queue is ok
        expected = {
            l_1.id: [],
            l_2.id: [msg_to_send]
        }
        self.assertEqual(expected, c.queues)


class StreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = SSEChannel()

    async def test_message_stream(self):
        c = self.sut
        listener = c.add_listener(MessageQueueListenerMock)
        await listener.start()

        c.dispatch(listener, Message(type='test', payload={'a': 1}))
        async for msg in await c.message_stream(listener):
            self.assertDictEqual({'data': {'a': 1}, 'event': 'test', 'retry': c.retry_timeout_millisedonds}, msg)
            self.assertDictEqual({listener.id: []}, c.queues)
            await listener.stop()


    async def test_watch(self):
        c = self.sut
        msg1 = Message('test', {'a': 1})
        msg2 = Message('test', {'a': 1})

        listener = MessageQueueListenerMock(
            num_messages_before_disconnect=1, fixtures={1: msg1, 2: msg2}
        )
        c.register_listener(listener)

        c.dispatch(listener, msg1)
        c.dispatch(listener, msg2)

        await listener.start()
