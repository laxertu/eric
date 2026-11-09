import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.entities import AbstractChannel
from eric_sse.exception import NoMessagesException
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.queues import Queue
from eric_sse.repository import ChannelRepository
from test.mock.failures import BrokenListener, BrokenQueue, RecordingListenerErrorHandler, RecordingQueuingErrorHandler


@dataclass
class Scenario:
    repository: ChannelRepository
    channel: AbstractChannel
    queuing_errors: RecordingQueuingErrorHandler
    listener_errors: RecordingListenerErrorHandler


def subscribe(channel: AbstractChannel) -> Connection:
    connection = channel.add_connection()
    connection.listener.start()
    return connection


class ChannelErrorHandlingContract(ABC):
    """
    Use cases every channel class has to satisfy when queues and listeners fail.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder` for the channel class. Tests replace its
    listeners and queues with failing ones where needed::

        class MyChannelTestCase(ChannelErrorHandlingContract, IsolatedAsyncioTestCase):
            def create_builder(self):
                return ChannelRepositoryBuilder(MyChannel)

            def channel_data(self):
                return {}

    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self) -> ChannelRepositoryBuilder:
        """Returns the builder under test. Called once per scenario."""
        pass

    @abstractmethod
    def channel_data(self) -> dict:
        """Returns the data passed to the built repository's ``create``, see ``ChannelRepositoryContract``."""
        pass

    def _scenario(
            self,
            listeners: Callable[[], MessageQueueListener] | None = None,
            queues: Callable[[], Queue] | None = None
    ) -> Scenario:
        queuing_errors, listener_errors = RecordingQueuingErrorHandler(), RecordingListenerErrorHandler()
        builder = self.create_builder().queuing_error_handler(queuing_errors).listener_error_handler(listener_errors)
        if listeners is not None:
            builder.listeners(listeners)
        if queues is not None:
            builder.queues(queues)
        repository = builder.build()
        return Scenario(repository, repository.create(self.channel_data()), queuing_errors, listener_errors)

    async def test_failed_push_is_reported_and_raised(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(queues=BrokenQueue)
        connection = subscribe(scenario.channel)

        with self.assertRaises(RuntimeError):
            scenario.channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual([('push', connection.id, 'test', 'push failed')], scenario.queuing_errors.events)

    async def test_broadcast_reaches_healthy_connections_after_a_failed_push(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario()
        channel = scenario.channel
        healthy = subscribe(channel)
        broken = Connection(listener=MessageQueueListener(), queue=BrokenQueue())
        channel.register_connection(broken)

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(healthy.id).type)
        self.assertEqual([('push', broken.id, 'test', 'push failed')], scenario.queuing_errors.events)

    async def test_handler_can_remove_the_failing_connection_during_a_broadcast(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        class RemovesFailingConnection(QueuingErrorHandler):
            def handle_push_error(self, connection_id, msg, exception):
                channel.remove_connection(connection_id)

        repository = self.create_builder().queuing_error_handler(RemovesFailingConnection()).build()
        channel = repository.create(self.channel_data())
        for _ in range(2):
            channel.register_connection(Connection(listener=MessageQueueListener(), queue=BrokenQueue()))
        healthy = subscribe(channel)

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(healthy.id).type)
        self.assertEqual([healthy], list(channel.get_connections()))

    async def test_handler_can_remove_other_connections_during_a_broadcast(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        class RemovesEveryConnection(QueuingErrorHandler):
            def handle_push_error(self, connection_id, msg, exception):
                for connection in list(channel.get_connections()):
                    channel.remove_connection(connection.id)

        repository = self.create_builder().queuing_error_handler(RemovesEveryConnection()).build()
        channel = repository.create(self.channel_data())
        for _ in range(2):
            channel.register_connection(Connection(listener=MessageQueueListener(), queue=BrokenQueue()))
        subscribe(channel)

        channel.broadcast(Message(msg_type='test'))

        self.assertEqual([], list(channel.get_connections()))

    async def test_failed_read_is_reported_and_raised(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(queues=BrokenQueue)
        connection = subscribe(scenario.channel)

        with self.assertRaises(RuntimeError):
            scenario.channel.deliver_next(connection.id)
        with self.assertRaises(RuntimeError):
            await scenario.channel.wait_next(connection.id, timeout=0.01)

        self.assertEqual(
            [('pop', connection.id, 'pop failed'), ('pop', connection.id, 'wait_pop failed')],
            scenario.queuing_errors.events
        )

    async def test_empty_queue_is_neither_reported_nor_logged(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario()
        connection = subscribe(scenario.channel)

        with self.assertNoLogs(level=logging.ERROR):
            with self.assertRaises(NoMessagesException):
                scenario.channel.deliver_next(connection.id)
            with self.assertRaises(NoMessagesException):
                await scenario.channel.wait_next(connection.id, timeout=0.01)

        self.assertEqual([], scenario.queuing_errors.events)

    async def test_raised_errors_are_left_to_the_caller_to_log(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(queues=BrokenQueue)
        channel = scenario.channel
        connection = subscribe(channel)

        with self.assertNoLogs(level=logging.ERROR):
            with self.assertRaises(RuntimeError):
                channel.dispatch(connection.id, Message(msg_type='test'))
            with self.assertRaises(RuntimeError):
                channel.deliver_next(connection.id)
            with self.assertRaises(RuntimeError):
                await channel.wait_next(connection.id, timeout=0.01)

    async def test_swallowed_errors_are_logged_with_their_traceback(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(listeners=BrokenListener)
        channel = scenario.channel
        connection = subscribe(channel)
        channel.register_connection(Connection(listener=MessageQueueListener(), queue=BrokenQueue()))

        with self.assertLogs(level=logging.DEBUG) as logs:
            channel.broadcast(Message(msg_type='test'))
            channel.deliver_next(connection.id)

        self.assertEqual(
            ['push failed', 'on_message failed'],
            [record.getMessage() for record in logs.records if record.levelno == logging.ERROR]
        )
        tracebacks = [record.getMessage() for record in logs.records if record.getMessage().startswith('Traceback')]
        self.assertEqual(2, len(tracebacks))
        self.assertIn('push failed', tracebacks[0])

    async def test_stream_logs_unexpected_errors_once_and_hides_their_details(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(queues=BrokenQueue)
        channel = scenario.channel
        channel.wait_timeout_seconds = 0.01
        connection = subscribe(channel)

        with self.assertLogs(level=logging.ERROR) as logs:
            stream = channel.message_stream(connection.id)
            event = await anext(stream)
            connection.listener.stop()
            await stream.aclose()

        self.assertEqual(['wait_pop failed'], [record.getMessage() for record in logs.records])
        self.assertNotIn('wait_pop failed', str(event))

    async def test_handlers_are_called_in_registration_order(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        calls = []

        class Handler(QueuingErrorHandler):
            def __init__(self, name):
                self.name = name

            def handle_push_error(self, connection_id, msg, exception):
                calls.append(self.name)

        repository = (
            self.create_builder()
            .queues(BrokenQueue)
            .queuing_error_handler(Handler('first'))
            .queuing_error_handler(Handler('second'))
            .build()
        )
        channel = repository.create(self.channel_data())
        connection = subscribe(channel)

        with self.assertRaises(RuntimeError):
            channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual(['first', 'second'], calls)

    async def test_message_the_listener_fails_to_handle_is_reported_and_delivered(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(listeners=BrokenListener)
        channel = scenario.channel
        connection = subscribe(channel)
        channel.dispatch(connection.id, Message(msg_type='first'))
        channel.dispatch(connection.id, Message(msg_type='second'))

        self.assertEqual('first', channel.deliver_next(connection.id).type)
        self.assertEqual('second', (await channel.wait_next(connection.id, timeout=0.01)).type)
        self.assertEqual(
            [('on_message', connection.id, 'first', 'on_message failed'), ('on_message', connection.id, 'second', 'on_message failed')],
            scenario.listener_errors.events
        )

    async def test_default_handlers_do_not_change_delivery(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        repository = (
            self.create_builder()
            .listeners(BrokenListener)
            .queuing_error_handler(QueuingErrorHandler())
            .listener_error_handler(ListenerErrorHandler())
            .build()
        )
        channel = repository.create(self.channel_data())
        connection = subscribe(channel)
        channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual('test', channel.deliver_next(connection.id).type)

    async def test_queuing_errors_are_reported_on_created_and_loaded_channels(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(queues=BrokenQueue)
        repository, created = scenario.repository, scenario.channel
        connection = created.add_connection()
        repository.persist(created)

        for channel in (created, repository.load_one(created.id), next(iter(repository.load_all()))):
            with self.assertRaises(RuntimeError):
                channel.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual(3, len(scenario.queuing_errors.events))

    async def test_listener_errors_are_reported_on_loaded_channels(self: 'ChannelErrorHandlingContract | IsolatedAsyncioTestCase'):
        scenario = self._scenario(listeners=BrokenListener)
        connection = scenario.channel.add_connection()
        scenario.repository.persist(scenario.channel)

        loaded = scenario.repository.load_one(scenario.channel.id)
        loaded.get_connection(connection.id).listener.start()
        loaded.dispatch(connection.id, Message(msg_type='test'))

        self.assertEqual('test', loaded.deliver_next(connection.id).type)
        self.assertEqual([('on_message', connection.id, 'test', 'on_message failed')], scenario.listener_errors.events)
