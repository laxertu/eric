from unittest import TestCase
from pytest import raises
from eric import Eric, InvalidChannelException, Message, InvalidListenerException, MessageQueueListener
from unittest import IsolatedAsyncioTestCase

class MessageQueueListenerMock(MessageQueueListener):

    def __init__(self, num_messages_before_disconnect=1, fixtures: dict[int, Message] = None):
        super().__init__()
        self.disconnect_after = num_messages_before_disconnect
        self.num_received = 0
        self.last_msg: Message | None = None
        self.fixtures = fixtures

    async def start(self):
        pass

    async def is_running(self) -> bool:
        return self.num_received >= self.disconnect_after

    async def stop(self) -> None:
        pass

    def on_message(self, msg: Message) -> None:
        self.num_received += 1
        self.last_msg = msg
        if self.fixtures is not None and self.fixtures.get(self.num_received):
            assert msg.type == self.last_msg.type
            assert msg.payload == self.last_msg.payload

    def close(self) -> None:
        pass


class EricTestCase(TestCase):

    def setUp(self):
        self.sut = Eric()

    def test_register_channel(self):

        sut = Eric()
        sut.register_channel('1')
        self.assertDictEqual({}, sut.channels['1'].listeners)


    def test_no_channel(self):
        with raises(InvalidChannelException):
            self.sut.get_channel(channel_id="unexixtent").dispatch(
                listener=MessageQueueListenerMock(), msg=Message(type='test')
            )

    def test_no_listener(self):
        sut = self.sut

        with raises(InvalidListenerException):
            sut.register_channel(channel_id='1')
            l = MessageQueueListenerMock()
            sut.get_channel('1').dispatch(l, msg=Message(type='test'))

    def test_broadcast_no_listeners(self):
        sut = self.sut
        sut.register_channel('1')
        sut.get_channel('1').broadcast(msg=Message(type= 'test'))
        self.assertDictEqual({}, sut.channels['1'].queues)

    def test_broadcast_ok(self):

        # scenario is: 1 channel and 2 listeners
        sut = self.sut
        c = sut.register_channel('channelid')
        l_1 = c.add_listener(MessageQueueListenerMock)
        l_2 = c.add_listener(MessageQueueListenerMock)

        # 1 broadcast
        msg_to_send = Message(type= 'test', payload={})
        c.broadcast(msg=msg_to_send)
        expected = {
            l_1.id: [msg_to_send],
            l_2.id: [msg_to_send]
        }
        self.assertEqual(expected, sut.channels['channelid'].queues)

        # message is received correctly
        msg_received = sut.get_channel('channelid').deliver_next(listener_id=l_1.id)
        self.assertEqual(msg_to_send, msg_received)

        # queue is ok
        expected = {
            l_1.id: [],
            l_2.id: [msg_to_send]
        }
        self.assertEqual(expected, sut.channels['channelid'].queues)


    def test_delete(self):
        sut = self.sut
        sid = 'channelid'
        c = sut.register_channel(sid)
        listener = c.add_listener(MessageQueueListenerMock)
        sut.get_channel(sid).dispatch(listener=listener, msg=Message(type='test'))
        sut.delete_channel(sid)

        self.assertDictEqual({}, sut.channels)

class StreamTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        Eric.QUEUES = {}
        self.sut = Eric()

    async def test_message_stream(self):
        sut = self.sut
        ch_id = 'channelid'
        c = sut.register_channel(channel_id=ch_id)
        listener = c.add_listener(MessageQueueListenerMock)
        await listener.start()

        sut.get_channel(ch_id).dispatch(listener, Message(type='test', payload={'a': 1}))
        async for msg in await sut.get_channel(ch_id).message_stream(listener):
            self.assertDictEqual({'data': {'a': 1}, 'event': 'test', 'retry': c.retry_timeout_millisedonds}, msg)
            self.assertDictEqual({listener.id: []}, sut.channels[ch_id].queues)
            await listener.stop()


    async def test_watch(self):
        sut = self.sut
        sid = 'channelid'
        c = sut.register_channel(channel_id=sid)
        msg1 = Message('test', {'a': 1})
        msg2 = Message('test', {'a': 1})

        listener = MessageQueueListenerMock(
            num_messages_before_disconnect=1, fixtures={1: msg1, 2: msg2}
        )
        c.register_listener(listener)

        sut.get_channel(sid).dispatch(listener, msg1)
        sut.get_channel(sid).dispatch(listener, msg2)

        await listener.start()
