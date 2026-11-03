import asyncio
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from test.mock.channel import FakeChannel
from test.mock.listener import MessageQueueListenerMock


class RecordingChannel(FakeChannel):
    wait_timeout_seconds = 0.05

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events = []
        self.go_on_after_error = True

    def on_listener_added(self, listener):
        self.events.append(('added', listener.id))

    def on_listener_removed(self, listener):
        self.events.append(('removed', listener.id))

    def on_stream_start(self, listener):
        self.events.append(('stream_start', listener.id))

    def on_stream_end(self, listener):
        self.events.append(('stream_end', listener.id))

    def before_dispatch(self, listener_id: str, msg: MessageContract) -> MessageContract | None:
        if msg.type == 'spam':
            return None
        if msg.type == 'shout':
            return Message(msg_type='shout', msg_payload=str(msg.payload).upper())
        return msg

    def on_error(self, listener, exception) -> bool:
        self.events.append(('error', str(exception)))
        return self.go_on_after_error


class SubscriptionHooksTestCase(IsolatedAsyncioTestCase):

    async def test_added_and_removed(self):
        sut = RecordingChannel()
        created = sut.add_listener()
        registered = MessageQueueListener()
        sut.register_listener(registered)
        sut.remove_listener(created.id)

        self.assertEqual([('added', created.id), ('added', registered.id), ('removed', created.id)], sut.events)

    async def test_not_called_when_loading_from_persistence(self):
        repository = ChannelRepositoryBuilder(RecordingChannel).build()
        channel = repository.create({})
        channel.add_listener()
        repository.persist(channel)

        self.assertEqual([], repository.load_one(channel.id).events)


class DispatchHookTestCase(IsolatedAsyncioTestCase):

    async def test_drop_and_transform(self):
        sut = RecordingChannel()
        listener = sut.add_listener()
        listener.start()
        sut.dispatch(listener.id, Message(msg_type='spam'))
        sut.broadcast(Message(msg_type='shout', msg_payload='hi'))

        self.assertEqual('HI', sut.deliver_next(listener.id).payload)
        with self.assertRaises(NoMessagesException):
            sut.deliver_next(listener.id)


class StreamHooksTestCase(IsolatedAsyncioTestCase):

    async def test_start_and_end(self):
        sut = RecordingChannel()
        listener = MessageQueueListenerMock()  # Stops itself after one message
        sut.register_listener(listener)
        sut.dispatch(listener.id, Message(msg_type='test'))
        sut.events.clear()

        [m async for m in sut.message_stream(listener)]
        self.assertEqual([('stream_start', listener.id), ('stream_end', listener.id)], sut.events)

    async def test_end_on_client_disconnection(self):
        sut = RecordingChannel()
        listener = sut.add_listener()
        sut.dispatch(listener.id, Message(msg_type='test'))

        stream = sut.message_stream(listener)
        await stream.__anext__()
        await stream.aclose()  # What a server does when the client goes away
        self.assertEqual(('stream_end', listener.id), sut.events[-1])

    async def _stream_with_failing_queue(self, sut: RecordingChannel, fail_times: int):
        listener = sut.add_listener()
        queue = sut._get_queue(listener.id)
        original_wait_pop = queue.wait_pop
        failures = {'left': fail_times}

        async def failing_wait_pop(timeout):
            if failures['left'] > 0:
                failures['left'] -= 1
                raise RuntimeError('backend down')
            return await original_wait_pop(timeout)

        queue.wait_pop = failing_wait_pop
        sut.dispatch(listener.id, Message(msg_type='test'))
        asyncio.get_running_loop().call_later(0.5, listener.stop)
        return [m.type async for m in sut.message_stream(listener)]

    async def test_error_goes_on_with_a_pause(self):
        sut = RecordingChannel()
        start = asyncio.get_running_loop().time()
        received = await self._stream_with_failing_queue(sut, fail_times=2)

        self.assertEqual(['error', 'error', 'test'], received)
        self.assertEqual(2, len([e for e in sut.events if e == ('error', 'backend down')]))
        self.assertGreaterEqual(asyncio.get_running_loop().time() - start, 2 * sut.wait_timeout_seconds)

    async def test_error_ends_stream(self):
        sut = RecordingChannel()
        sut.go_on_after_error = False
        received = await self._stream_with_failing_queue(sut, fail_times=1)

        self.assertEqual(['error'], received)
        self.assertEqual('stream_end', sut.events[-1][0])
