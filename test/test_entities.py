import asyncio
from unittest import TestCase, IsolatedAsyncioTestCase

import pytest

from eric_sse.exception import InvalidListenerException, NoMessagesException
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
        listener = fake_channel.add_listener()

        with self.assertRaises(NoMessagesException):
            fake_channel.deliver_next(listener.id)

        listener.start()
        with self.assertRaises(NoMessagesException):
            fake_channel.deliver_next(listener.id)

        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(1, len(connections))
        self.assertIs(connections[0].listener, listener)

        listener2 = MessageQueueListener()
        fake_channel.register_listener(listener2)

        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(2, len(connections))
        self.assertIs(connections[0].listener, listener)
        self.assertIs(connections[1].listener, listener2)

        fake_channel.remove_listener(listener.id)
        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual(1, len(connections))
        self.assertIs(connections[0].listener, listener2)
        self.assertIs(fake_channel.get_listener(listener2.id), listener2)

        fake_channel.register_connection(
            Connection(listener=MessageQueueListener(listener_id='test'), queue=InMemoryQueue())
        )
        connections = [connection for connection in fake_channel.get_connections()]
        self.assertEqual('test', connections[-1].listener.id)

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
        self.assertEqual(listener.id, connection.listener.id)
        connection = sut.create()
        self.assertIsInstance(connection, Connection)
        self.assertIsInstance(connection.listener, MessageQueueListener)
        self.assertIsInstance(connection.queue, InMemoryQueue)

    def test_listener_deletion(self):
        sut = SSEChannel()
        with self.assertRaises(InvalidListenerException):
            sut.remove_listener('fake')


class AbstractChannelTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sut = FakeChannel()

    def test_model_is_consistent(self):
        listener1 = self.sut.add_listener()
        listener2 = self.sut.add_listener()

        listeners = set([c.listener for c in self.sut.get_connections()])
        self.assertEqual(2, len(listeners))
        self.assertTrue(listener1 in listeners)
        self.assertTrue(listener2 in listeners)
        self.assertIs(listener1, self.sut.get_listener(listener1.id))
        self.assertIs(listener2, self.sut.get_listener(listener2.id))


    def test_error_handling(self):

        with self.assertRaises(InvalidListenerException):
            self.sut.remove_listener('fake')

        with self.assertRaises(InvalidListenerException):
            self.sut.get_listener('fake')

        with self.assertRaises(InvalidListenerException):
            self.sut.dispatch('fake', Message(msg_type='test'))

    async def test_error_handling_async(self):
        listener = MessageQueueListener()

        with pytest.raises(InvalidListenerException):
            async for _ in self.sut.message_stream(listener):
                pass

    async def test_stream_starts_listener(self):
        listener = MessageQueueListenerMock()  # Stops itself after one message
        self.sut.register_listener(listener)
        self.sut.dispatch(listener_id=listener.id, msg=Message(msg_type='test'))
        self.assertFalse(listener.is_running())

        received = [m async for m in self.sut.message_stream(listener)]
        self.assertEqual(1, len(received))
        self.assertFalse(listener.is_running())

    async def test_stream_ends_with_error_when_listener_is_removed(self):
        self.sut.wait_timeout_seconds = 0.05
        listener = self.sut.add_listener()
        asyncio.get_running_loop().call_later(0.01, self.sut.remove_listener, listener.id)

        received = [m async for m in self.sut.message_stream(listener)]
        self.assertEqual(1, len(received))
        self.assertIsInstance(received[0], InvalidListenerException)

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


