import asyncio
from abc import ABC, abstractmethod
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.connection import Connection
from eric_sse.entities import AbstractChannel
from eric_sse.exception import InvalidConnectionException, NoMessagesException, StoppedListenerException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract, SignedMessage
from eric_sse.queues import InMemoryQueue


class StoppedAfterCheckListener(MessageQueueListener):
    """Running for the stream loop check, stopped when the channel waits: as if stopped by another thread in between."""
    def __init__(self):
        super().__init__()
        self.answers = iter([True])

    def is_running(self) -> bool:
        return next(self.answers, False)


class StopsAfterOneMessage(MessageQueueListener):
    def on_message(self, msg: MessageContract) -> None:
        self.stop()


class ChannelContract(ABC):
    """
    Use cases every channel class has to satisfy: managing connections and delivering messages.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder` for the channel class::

        class MyChannelTestCase(ChannelContract, IsolatedAsyncioTestCase):
            def create_builder(self):
                return ChannelRepositoryBuilder(MyChannel)

            def channel_data(self):
                return {}

    Streamed events are compared with the channel's own ``adapt``, as their format is up to each channel.
    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self) -> ChannelRepositoryBuilder:
        """Returns the builder under test. Called once per test."""
        pass

    @abstractmethod
    def channel_data(self) -> dict:
        """Returns the data passed to the built repository's ``create``, see ``ChannelRepositoryContract``."""
        pass

    def _create_channel(self, builder: ChannelRepositoryBuilder | None = None) -> AbstractChannel:
        builder = builder if builder is not None else self.create_builder()
        return builder.build().create(self.channel_data())

    def test_delivered_message_keeps_its_content(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        connection = channel.add_connection()
        connection.listener.start()

        for sent in (
            Message(msg_type='test'),
            Message(msg_type='test', msg_payload={'a': 1}, msg_id='message_id'),
            SignedMessage(sender_id='sender_id', msg_type='test', msg_payload={'a': 1}, msg_id='message_id'),
        ):
            channel.dispatch(connection.id, sent)
            received = channel.deliver_next(connection.id)
            self.assertEqual((sent.type, sent.payload, sent.id), (received.type, received.payload, received.id))

    def test_signed_message_keeps_its_sender(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        connection = channel.add_connection()
        connection.listener.start()

        channel.dispatch(connection.id, SignedMessage(sender_id='sender_id', msg_type='test'))

        self.assertEqual('sender_id', channel.deliver_next(connection.id).sender_id)

    def test_delivery_requires_a_running_listener_before_checking_for_messages(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        connection = channel.add_connection()

        with self.assertRaises(StoppedListenerException):
            channel.deliver_next(connection.id)

        connection.listener.start()
        with self.assertRaises(NoMessagesException):
            channel.deliver_next(connection.id)

    async def test_waiting_requires_a_running_listener(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        connection = channel.add_connection()

        with self.assertRaises(StoppedListenerException):
            await channel.wait_next(connection.id, 0.05)

    async def test_stream_reports_an_error_and_ends_when_the_listener_stops_before_waiting(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel(self.create_builder().listeners(StoppedAfterCheckListener))
        connection = channel.add_connection()

        received = [event async for event in channel.message_stream(connection.id)]

        self.assertEqual(1, len(received))

    def test_connections_are_added_and_registered_until_removed(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        added = channel.add_connection()
        listener = MessageQueueListener()
        registered = channel.register_listener(listener)

        self.assertCountEqual([added, registered], channel.get_connections())
        self.assertIs(added, channel.get_connection(added.id))
        self.assertIs(listener, channel.get_connection(registered.id).listener)

        channel.remove_connection(added.id)

        self.assertEqual([registered], list(channel.get_connections()))

    def test_existing_connection_is_reachable_by_its_id(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        connection = Connection(listener=MessageQueueListener(), queue=InMemoryQueue(), connection_id='my_id')

        channel.register_connection(connection)

        self.assertIs(connection, channel.get_connection('my_id'))

    async def test_unknown_connections_are_rejected(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()

        with self.assertRaises(InvalidConnectionException):
            channel.get_connection('unknown')
        with self.assertRaises(InvalidConnectionException):
            channel.remove_connection('unknown')
        with self.assertRaises(InvalidConnectionException):
            channel.dispatch('unknown', Message(msg_type='test'))
        with self.assertRaises(InvalidConnectionException):
            async for _ in channel.message_stream('unknown'):
                pass

    async def test_stream_starts_the_listener_and_ends_when_it_stops(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel(self.create_builder().listeners(StopsAfterOneMessage))
        connection = channel.add_connection()
        message = Message(msg_type='test')
        channel.dispatch(connection.id, message)
        self.assertFalse(connection.listener.is_running())

        received = [event async for event in channel.message_stream(connection.id)]

        self.assertEqual([channel.adapt(message)], received)
        self.assertFalse(connection.listener.is_running())

    async def test_stream_reports_an_error_and_ends_when_its_connection_is_removed(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        channel.wait_timeout_seconds = 0.05
        connection = channel.add_connection()
        asyncio.get_running_loop().call_later(0.01, channel.remove_connection, connection.id)

        received = [event async for event in channel.message_stream(connection.id)]

        self.assertEqual(1, len(received))

    async def test_watching_receives_broadcasts_and_leaves_no_connection_behind(self: 'ChannelContract | IsolatedAsyncioTestCase'):
        channel = self._create_channel()
        message = Message(msg_type='test')
        stream = channel.watch()
        asyncio.get_running_loop().call_later(0.01, channel.broadcast, message)

        received = await anext(stream)
        await stream.aclose()

        self.assertEqual(channel.adapt(message), received)
        self.assertEqual([], list(channel.get_connections()))
