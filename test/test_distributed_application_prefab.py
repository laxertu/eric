from unittest import IsolatedAsyncioTestCase

from eric_sse.message import MessageContract, Message
from eric_sse.prefabs import SimpleDistributedApplicationChannel, SimpleDistributedApplicationListener, DataProcessingChannel


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


class DistributedListenerTestCase(IsolatedAsyncioTestCase):

    @staticmethod
    async def create_listener(ch: SimpleDistributedApplicationChannel):
        l = SimpleDistributedApplicationListener()
        l.set_action('hello', hello_response)
        l.set_action('hello_ack', hello_ack_response)
        l.start()
        ch.register_listener(l)
        return l


    async def test_application(self):
        ssc = SimpleDistributedApplicationChannel()

        alice = await DistributedListenerTestCase.create_listener(ssc)
        bob = await DistributedListenerTestCase.create_listener(ssc)


        # Bob says hello to Alice
        bob.dispatch_to(alice, Message(msg_type='hello', msg_payload='hello!'))

        # Alice will stop after having answered to Bob
        bob.dispatch_to(alice, Message(msg_type='stop'))

        types = [m['event'] async for m in ssc.message_stream(alice)]
        self.assertEqual(['hello', 'stop'], types)

        types = [m['event'] async for m in ssc.message_stream(bob)]
        self.assertEqual(['hello_ack', 'stop'], types)

class SetActionTestCase(IsolatedAsyncioTestCase):
    async def test_internal_actions_cannot_be_overridden(self):
        listener = SimpleDistributedApplicationListener()
        for name in ('start', 'stop'):
            with self.assertRaises(KeyError):
                listener.set_action(name, hello_response)


class DataProcessingChannelTestCase(IsolatedAsyncioTestCase):
    async def test_channel(self):
        channel = DataProcessingChannel(stream_delay_seconds=0, max_workers=2)
        listener = MessageQueueListenerMock()
        channel.register_listener(listener=listener)

        channel.dispatch(listener.id, Message(msg_type='test1'))
        channel.dispatch(listener.id, Message(msg_type='test2'))
        channel.dispatch(listener.id, Message(msg_type='test3'))

        listener.start()
        types = {m['event'] async for m in channel.process_queue(listener)}
        self.assertEqual({'test1', 'test2', 'test3'}, types)


class ListenerChannelTestCase(IsolatedAsyncioTestCase):

    async def test_dispatch_without_channel_raises_a_clear_error(self):
        from eric_sse.exception import InvalidChannelException
        with self.assertRaises(InvalidChannelException):
            SimpleDistributedApplicationListener().dispatch_to(MessageQueueListenerMock(), Message(msg_type='hello'))

    async def test_channel_is_set_on_created_and_loaded_listeners(self):
        from eric_sse.builder import ChannelRepositoryBuilder
        repository = (
            ChannelRepositoryBuilder()
            .channels(SimpleDistributedApplicationChannel)
            .listeners(SimpleDistributedApplicationListener)
            .build()
        )
        channel = repository.create({})
        alice = channel.add_listener()
        bob = channel.add_listener()
        repository.persist(channel)

        loaded = repository.load_one(channel.id)
        loaded_alice = loaded.get_listener(alice.id)
        loaded_alice.set_action('hello', hello_response)
        loaded_bob = loaded.get_listener(bob.id)
        loaded_bob.dispatch_to(loaded_alice, Message(msg_type='hello', msg_payload='hi'))
        loaded_bob.dispatch_to(loaded_alice, Message(msg_type='stop'))

        types = [m['event'] async for m in loaded.message_stream(loaded_alice)]
        self.assertEqual(['hello', 'stop'], types)
        # Alice answered through the loaded channel
        self.assertEqual("hello_ack", loaded._get_queue(bob.id).pop().type)
