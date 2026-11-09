import asyncio
from unittest import TestCase, IsolatedAsyncioTestCase

import pytest

from eric_sse.exception import InvalidConnectionException, NoMessagesException, StoppedListenerException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, SignedMessage
from eric_sse.connection import Connection, InMemoryConnectionsFactory
from eric_sse.queues import InMemoryQueue
from eric_sse.prefabs import SSEChannel
from test.mock.channel import FakeChannel
from test.mock.listener import MessageQueueListenerMock


class MessageContractImplementationsTestCase(TestCase):

    def test_model_is_consistent(self):

        m = Message(msg_type='test')
        self.assertEqual('test', m.type)
        self.assertIsNone(m.payload)

        m = Message(msg_type='test', msg_payload={'a': 1})
        self.assertEqual('test', m.type)
        self.assertEqual({'a': 1}, m.payload)

        m = SignedMessage(msg_type='test', sender_id='sender_id')
        self.assertEqual('test', m.type)
        self.assertEqual('sender_id', m.sender_id)

        m = SignedMessage(msg_type='test', msg_payload={'a': 1}, sender_id='sender_id')
        self.assertEqual('test', m.type)
        self.assertEqual('sender_id', m.sender_id)
        self.assertEqual({'a': 1}, m.payload)

        m = SignedMessage(msg_type='test', sender_id='sender_id', msg_id='message_id')
        self.assertEqual('message_id', m.id)

        m = Message(msg_type='test', msg_payload={'a': 1}, msg_id='message_id')
        self.assertEqual('message_id', m.id)
        self.assertEqual('test', m.type)
        self.assertEqual({'a': 1}, m.payload)

        self.assertIsNone(Message(msg_type='test').id)

    def test_listeners_management(self):

        fake_channel = FakeChannel()
        first = fake_channel.add_connection()

        # Stopped listener with an empty queue: being stopped comes first
        with self.assertRaises(StoppedListenerException):
            fake_channel.deliver_next(first.id)

        first.listener.start()
        with self.assertRaises(NoMessagesException):
            fake_channel.deliver_next(first.id)

        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(1, len(connections))
        self.assertIs(connections[0], first)

        listener2 = MessageQueueListener()
        listener2_connection = fake_channel.register_listener(listener2)

        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(2, len(connections))
        self.assertIs(connections[0], first)
        self.assertIs(connections[1].listener, listener2)

        fake_channel.remove_connection(first.id)
        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(1, len(connections))
        self.assertIs(connections[0].listener, listener2)
        self.assertIs(fake_channel.get_connection(listener2_connection.id).listener, listener2)

        fake_channel.register_connection(
            Connection(listener=MessageQueueListener(), queue=InMemoryQueue(), connection_id='test')
        )
        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual('test', connections[-1].id)

class QueueTstCase(TestCase):

    def test_in_memory_queue(self):
        sut = InMemoryQueue()
        sut.push(Message(msg_type='test'))
        self.assertEqual('test', sut.pop().type)

class ConnectionsTestCase(TestCase):

    def test_model_is_consistent(self):
        sut = Connection(listener=MessageQueueListener(), queue=InMemoryQueue(), connection_id='test')
        self.assertEqual('test', sut.id)

    def test_in_memory_factory(self):
        sut = InMemoryConnectionsFactory()
        listener = MessageQueueListener()
        connection = sut.create(listener=listener)
        self.assertIs(listener, connection.listener)
        connection = sut.create()
        self.assertIsInstance(connection, Connection)
        self.assertIsInstance(connection.listener, MessageQueueListener)
        self.assertIsInstance(connection.queue, InMemoryQueue)

    def test_listener_deletion(self):
        sut = SSEChannel()
        with self.assertRaises(InvalidConnectionException):
            sut.remove_connection('fake')


class AbstractChannelTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = FakeChannel()

    def test_model_is_consistent(self):
        connection1 = self.sut.add_connection()
        connection2 = self.sut.add_connection()

        self.assertEqual({connection1, connection2}, set(self.sut.get_connections()))
        self.assertIs(connection1, self.sut.get_connection(connection1.id))
        self.assertIs(connection2, self.sut.get_connection(connection2.id))


    def test_error_handling(self):

        with self.assertRaises(InvalidConnectionException):
            self.sut.remove_connection('fake')

        with self.assertRaises(InvalidConnectionException):
            self.sut.get_connection('fake').listener

        with self.assertRaises(InvalidConnectionException):
            self.sut.dispatch('fake', Message(msg_type='test'))

    async def test_error_handling_async(self):
        with pytest.raises(InvalidConnectionException):
            async for _ in self.sut.message_stream('fake'):
                pass

    async def test_stream_starts_listener(self):
        listener = MessageQueueListenerMock()  # Stops itself after one message
        connection = self.sut.register_listener(listener)
        self.sut.dispatch(connection_id=connection.id, msg=Message(msg_type='test'))
        self.assertFalse(listener.is_running())

        received = [m async for m in self.sut.message_stream(connection.id)]
        self.assertEqual(1, len(received))
        self.assertFalse(listener.is_running())

    async def test_stream_ends_with_error_when_listener_is_removed(self):
        self.sut.wait_timeout_seconds = 0.05
        connection = self.sut.add_connection()
        asyncio.get_running_loop().call_later(0.01, self.sut.remove_connection, connection.id)

        received = [m async for m in self.sut.message_stream(connection.id)]
        self.assertEqual(1, len(received))
        self.assertIsInstance(received[0], InvalidConnectionException)

    async def test_watch(self):
        received = []
        stream = self.sut.watch()
        asyncio.get_running_loop().call_later(0.01, self.sut.broadcast, Message(msg_type='test'))
        async for m in stream:
            received.append(m)
            break
        await stream.aclose()

        self.assertEqual(['test'], [m.type for m in received])
        self.assertEqual(0, len(list(self.sut.get_connections())))  # Its listener is removed


