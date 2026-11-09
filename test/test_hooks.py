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

    def on_connection_added(self, connection):
        self.events.append(('added', connection.id))

    def on_connection_removed(self, connection):
        self.events.append(('removed', connection.id))

    def on_stream_start(self, connection):
        self.events.append(('stream_start', connection.id))

    def on_stream_end(self, connection):
        self.events.append(('stream_end', connection.id))

    def before_dispatch(self, connection_id: str, msg: MessageContract) -> MessageContract | None:
        if msg.type == 'spam':
            return None
        if msg.type == 'shout':
            return Message(msg_type='shout', msg_payload=str(msg.payload).upper())
        return msg

    def on_wait_timeout(self, connection):
        self.events.append(('wait_timeout', connection.id))

    def on_error(self, connection, exception) -> bool:
        self.events.append(('error', str(exception)))
        return self.go_on_after_error


class SubscriptionHooksTestCase(IsolatedAsyncioTestCase):

    async def test_added_and_removed(self):
        sut = RecordingChannel()
        created = sut.add_connection()
        registered = MessageQueueListener()
        connection = sut.register_listener(registered)
        sut.remove_connection(created.id)

        self.assertEqual([('added', created.id), ('added', connection.id), ('removed', created.id)], sut.events)

    async def test_not_called_when_loading_from_persistence(self):
        repository = ChannelRepositoryBuilder(RecordingChannel).build()
        channel = repository.create({})
        channel.add_connection()
        repository.persist(channel)

        self.assertEqual([], repository.load_one(channel.id).events)


class RegisteredListener(MessageQueueListener):
    def __init__(self):
        super().__init__()
        self.channels = []

    def on_registered(self, channel, connection_id) -> None:
        self.channels.append(channel)


class ListenerHooksTestCase(IsolatedAsyncioTestCase):

    async def test_on_registered(self):
        channel = FakeChannel()
        listener = RegisteredListener()
        channel.register_listener(listener)

        self.assertEqual([channel], listener.channels)

    async def test_on_registered_for_created_and_loaded_listeners(self):
        repository = ChannelRepositoryBuilder(FakeChannel).listeners(RegisteredListener).build()
        channel = repository.create({})
        connection = channel.add_connection()
        repository.persist(channel)

        loaded = repository.load_one(channel.id)

        self.assertEqual([channel, loaded], loaded.get_connection(connection.id).listener.channels)


class DispatchHookTestCase(IsolatedAsyncioTestCase):

    async def test_drop_and_transform(self):
        sut = RecordingChannel()
        connection = sut.add_connection()
        connection.listener.start()
        sut.dispatch(connection.id, Message(msg_type='spam'))
        sut.broadcast(Message(msg_type='shout', msg_payload='hi'))

        self.assertEqual('HI', sut.deliver_next(connection.id).payload)
        with self.assertRaises(NoMessagesException):
            sut.deliver_next(connection.id)


class StreamHooksTestCase(IsolatedAsyncioTestCase):

    async def test_start_and_end(self):
        sut = RecordingChannel()
        listener = MessageQueueListenerMock()  # Stops itself after one message
        connection = sut.register_listener(listener)
        sut.dispatch(connection.id, Message(msg_type='test'))
        sut.events.clear()

        [m async for m in sut.message_stream(connection.id)]
        self.assertEqual([('stream_start', connection.id), ('stream_end', connection.id)], sut.events)

    async def test_wait_timeout_while_idle(self):
        sut = RecordingChannel()
        connection = sut.add_connection()
        asyncio.get_running_loop().call_later(sut.wait_timeout_seconds * 2.5, connection.listener.stop)

        received = [m async for m in sut.message_stream(connection.id)]

        self.assertEqual([], received)
        # Timeouts at 1, 2 and 3 cycles: the stop at 2.5 is noticed after the third one
        self.assertEqual(3, sut.events.count(('wait_timeout', connection.id)))

    async def test_end_on_client_disconnection(self):
        sut = RecordingChannel()
        connection = sut.add_connection()
        sut.dispatch(connection.id, Message(msg_type='test'))

        stream = sut.message_stream(connection.id)
        await stream.__anext__()
        await stream.aclose()  # What a server does when the client goes away
        self.assertEqual(('stream_end', connection.id), sut.events[-1])

    async def _stream_with_failing_queue(self, sut: RecordingChannel, fail_times: int):
        connection = sut.add_connection()
        queue = sut.get_connection(connection.id).queue
        original_wait_pop = queue.wait_pop
        failures = {'left': fail_times}

        async def failing_wait_pop(timeout):
            if failures['left'] > 0:
                failures['left'] -= 1
                raise RuntimeError('backend down')
            return await original_wait_pop(timeout)

        queue.wait_pop = failing_wait_pop
        sut.dispatch(connection.id, Message(msg_type='test'))
        asyncio.get_running_loop().call_later(0.5, connection.listener.stop)
        return [type(m).__name__ if isinstance(m, Exception) else m.type async for m in sut.message_stream(connection.id)]

    async def test_error_goes_on_with_a_pause(self):
        sut = RecordingChannel()
        start = asyncio.get_running_loop().time()
        received = await self._stream_with_failing_queue(sut, fail_times=2)

        self.assertEqual(['InternalStreamError', 'InternalStreamError', 'test'], received)
        self.assertEqual(2, len([e for e in sut.events if e == ('error', 'backend down')]))
        self.assertGreaterEqual(asyncio.get_running_loop().time() - start, 2 * sut.wait_timeout_seconds)

    async def test_error_ends_stream(self):
        sut = RecordingChannel()
        sut.go_on_after_error = False
        received = await self._stream_with_failing_queue(sut, fail_times=1)

        self.assertEqual(['InternalStreamError'], received)
        self.assertEqual('stream_end', sut.events[-1][0])
