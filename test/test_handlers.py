from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.exception import NoMessagesException, InternalStreamError
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.queues import InMemoryQueue
from test.mock.channel import FakeChannel


class BrokenQueue(InMemoryQueue):
    def push(self, message: MessageContract) -> None:
        raise RuntimeError('push failed')

    def pop(self, timeout: float = 0) -> MessageContract:
        raise RuntimeError('pop failed')

    async def wait_pop(self, timeout: float) -> MessageContract:
        raise RuntimeError('wait_pop failed')


class BrokenListener(MessageQueueListener):
    def on_message(self, msg: MessageContract) -> None:
        raise RuntimeError('on_message failed')


class RecordingQueuingErrorHandler(QueuingErrorHandler):
    def __init__(self):
        self.events = []

    def handle_push_error(self, connection_id: str, msg: MessageContract, exception: Exception):
        self.events.append(('push', connection_id, msg.type, str(exception)))

    def handle_pop_error(self, connection_id: str, exception: Exception):
        self.events.append(('pop', connection_id, str(exception)))


class RecordingListenerErrorHandler(ListenerErrorHandler):
    def __init__(self):
        self.events = []

    def handle_on_message_error(self, connection_id: str, msg: MessageContract, exception: Exception):
        self.events.append(('on_message', connection_id, msg.type, str(exception)))


def channel_with_handlers():
    channel = FakeChannel()
    queuing_handler = RecordingQueuingErrorHandler()
    listener_handler = RecordingListenerErrorHandler()
    channel.add_queuing_error_handler(queuing_handler)
    channel.add_listener_error_handler(listener_handler)
    return channel, queuing_handler, listener_handler


def register_broken_queue(channel: FakeChannel) -> Connection:
    connection = Connection(listener=MessageQueueListener(), queue=BrokenQueue())
    channel.register_connection(connection)
    connection.listener.start()
    return connection


class QueuingErrorHandlerTestCase(IsolatedAsyncioTestCase):

    async def test_push_error_is_handled_and_reraised(self):
        channel, queuing_handler, _ = channel_with_handlers()
        connection = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual([('push', connection.id, 'test', 'push failed')], queuing_handler.events)

    async def test_broadcast_goes_on_after_push_error(self):
        channel, queuing_handler, _ = channel_with_handlers()
        broken = register_broken_queue(channel)
        healthy = channel.add_connection()
        healthy.listener.start()

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(healthy.id).type)
        self.assertEqual([('push', broken.id, 'test', 'push failed')], queuing_handler.events)

    async def test_pop_error_is_handled_and_reraised(self):
        channel, queuing_handler, _ = channel_with_handlers()
        connection = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.deliver_next(connection.id)
        with self.assertRaises(RuntimeError):
            await channel.wait_next(connection.id, timeout=0.01)

        self.assertEqual([('pop', connection.id, 'pop failed'), ('pop', connection.id, 'wait_pop failed')], queuing_handler.events)

    async def test_no_messages_is_not_handled_nor_logged(self):
        channel, queuing_handler, _ = channel_with_handlers()
        connection = channel.add_connection()
        connection.listener.start()

        with patch('eric_sse.entities.logger') as logger:
            with self.assertRaises(NoMessagesException):
                channel.deliver_next(connection.id)
            with self.assertRaises(NoMessagesException):
                await channel.wait_next(connection.id, timeout=0.01)

        logger.error.assert_not_called()
        self.assertEqual([], queuing_handler.events)

    async def test_reraised_errors_are_not_logged(self):
        channel, _, _ = channel_with_handlers()
        connection = register_broken_queue(channel)

        with patch('eric_sse.entities.logger') as logger:
            with self.assertRaises(RuntimeError):
                channel.dispatch(connection.id, Message(msg_type='test'))
            with self.assertRaises(RuntimeError):
                channel.deliver_next(connection.id)
            with self.assertRaises(RuntimeError):
                await channel.wait_next(connection.id, timeout=0.01)

        logger.error.assert_not_called()

    async def test_swallowed_errors_are_logged(self):
        channel, _, _ = channel_with_handlers()
        register_broken_queue(channel)
        listener = BrokenListener()
        connection = channel.register_listener(listener)
        listener.start()

        with patch('eric_sse.entities.logger') as logger:
            channel.broadcast(Message(msg_type='test'))
            channel.deliver_next(connection.id)

        self.assertEqual(2, logger.error.call_count)
        self.assertIn('push failed', logger.debug.call_args_list[0].args[0])

    async def test_errors_are_logged_once(self):
        channel, _, _ = channel_with_handlers()
        channel.wait_timeout_seconds = 0.01
        connection = register_broken_queue(channel)

        with patch('eric_sse.entities.logger') as logger:
            stream = channel.message_stream(connection.id)
            self.assertIsInstance(await anext(stream), InternalStreamError)
            connection.listener.stop()
            await stream.aclose()

        logger.error.assert_called_once()

    async def test_handlers_are_called_in_registration_order(self):
        channel = FakeChannel()
        calls = []

        class Handler(QueuingErrorHandler):
            def __init__(self, name):
                self.name = name

            def handle_push_error(self, connection_id, msg, exception):
                calls.append(self.name)

        channel.add_queuing_error_handler(Handler('first'))
        channel.add_queuing_error_handler(Handler('second'))
        connection = register_broken_queue(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual(['first', 'second'], calls)


class ListenerErrorHandlerTestCase(IsolatedAsyncioTestCase):

    async def test_on_message_error_is_handled_and_message_delivered(self):
        channel, _, listener_handler = channel_with_handlers()
        listener = BrokenListener()
        connection = channel.register_listener(listener)
        listener.start()
        channel.dispatch(connection.id, Message(msg_type='first'))
        channel.dispatch(connection.id, Message(msg_type='second'))

        self.assertEqual('first', channel.deliver_next(connection.id).type)
        self.assertEqual('second', (await channel.wait_next(connection.id, timeout=0.01)).type)
        self.assertEqual(
            [('on_message', connection.id, 'first', 'on_message failed'), ('on_message', connection.id, 'second', 'on_message failed')],
            listener_handler.events
        )

    async def test_default_handlers_do_nothing(self):
        channel = FakeChannel()
        channel.add_queuing_error_handler(QueuingErrorHandler())
        channel.add_listener_error_handler(ListenerErrorHandler())
        listener = BrokenListener()
        connection = channel.register_listener(listener)
        listener.start()
        channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(connection.id).type)


class BuilderErrorHandlersTestCase(IsolatedAsyncioTestCase):

    async def test_handlers_registered_on_created_and_loaded_channels(self):
        queuing_handler = RecordingQueuingErrorHandler()
        first_listener_handler = RecordingListenerErrorHandler()
        second_listener_handler = RecordingListenerErrorHandler()
        repository = (
            ChannelRepositoryBuilder(FakeChannel)
            .listeners(BrokenListener)
            .queues(BrokenQueue)
            .queuing_error_handler(queuing_handler)
            .listener_error_handler(first_listener_handler)
            .listener_error_handler(second_listener_handler)
            .build()
        )
        created = repository.create({})
        connection = created.add_connection()
        repository.persist(created)

        for channel in (created, repository.load_one(created.id), next(iter(repository.load_all()))):
            with self.assertRaises(RuntimeError):
                channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual(3, len(queuing_handler.events))

    async def test_listener_handlers_on_loaded_channel(self):
        handler = RecordingListenerErrorHandler()
        repository = (
            ChannelRepositoryBuilder(FakeChannel)
            .listeners(BrokenListener)
            .listener_error_handler(handler)
            .build()
        )
        channel = repository.create({})
        connection = channel.add_connection()
        repository.persist(channel)

        loaded = repository.load_one(channel.id)
        loaded.get_connection(connection.id).listener.start()
        loaded.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual('test', loaded.deliver_next(connection.id).type)
        self.assertEqual([('on_message', connection.id, 'test', 'on_message failed')], handler.events)
