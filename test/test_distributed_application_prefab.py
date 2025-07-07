from unittest import IsolatedAsyncioTestCase

import pytest

from eric_sse.message import MessageContract, Message
from eric_sse.prefabs import SSEChannel, SimpleDistributedApplicationListener, DataProcessingChannel

from test.mock.listener import MessageQueueListenerMock


def hello_response(m: MessageContract) -> list[Message]:
    return [
        Message(msg_type='hello_ack', msg_payload=f'{m.payload}!'),
        Message(msg_type='stop')
    ]

def hello_ack_response(m: MessageContract) -> list[Message]:
    return [
        Message(msg_type='stop')
    ]

#@pytest.mark.skip(reason="not implemented")
class DistributedListenerTestCase(IsolatedAsyncioTestCase):

    @staticmethod
    async def create_listener(ch: SSEChannel):
        l = SimpleDistributedApplicationListener(ch)
        l.set_action('hello', hello_response)
        l.set_action('hello_ack', hello_ack_response)
        l.start_sync()
        await ch.register_listener(l)
        return l


    async def test_application(self):
        ssc = SSEChannel()

        alice = await DistributedListenerTestCase.create_listener(ssc)
        bob = await DistributedListenerTestCase.create_listener(ssc)


        # Bob says hello to Alice
        await bob.dispatch_to(alice, Message(msg_type='hello', msg_payload='hello!'))

        # Alice will stop after having answered to Bob
        await bob.dispatch_to(alice, Message(msg_type='stop'))

        types = [m['event'] async for m in ssc.message_stream(alice)]
        self.assertEqual(['hello', 'stop'], types)

        types = [m['event'] async for m in ssc.message_stream(bob)]
        self.assertEqual(['hello_ack', 'stop'], types)

class DataProcessingChannelTestCase(IsolatedAsyncioTestCase):
    async def test_channel(self):
        channel = DataProcessingChannel(stream_delay_seconds=0, max_workers=2)
        listener = MessageQueueListenerMock()
        await channel.register_listener(listener)

        await channel.dispatch(listener.id, Message(msg_type='test1'))
        await channel.dispatch(listener.id, Message(msg_type='test2'))
        await channel.dispatch(listener.id, Message(msg_type='test3'))

        await listener.start()
        types = {m['event'] async for m in channel.process_queue(listener)}
        self.assertEqual({'test1', 'test2', 'test3'}, types)
