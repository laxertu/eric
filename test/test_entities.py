from unittest import TestCase, IsolatedAsyncioTestCase

import pytest

from eric_sse.exception import InvalidListenerException, NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, SignedMessage, UniqueMessage
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

        m = UniqueMessage(message_id='message_id', message=Message(msg_type='test', msg_payload={'a': 1}))
        self.assertEqual('message_id', m.id)
        self.assertEqual('test', m.type)
        self.assertEqual({'a': 1}, m.payload)

        m = UniqueMessage(message_id='message_id', message=Message(msg_type='test', msg_payload={'a': 1}), sender_id='sender_id')
        self.assertEqual('message_id', m.id)
        self.assertEqual('test', m.type)
        self.assertEqual({'a': 1}, m.payload)

        m1 = UniqueMessage(message=Message(msg_type='test', msg_payload={'a': 1}), sender_id='sender_id')
        m2 = UniqueMessage(message=Message(msg_type='test', msg_payload={'a': 1}), sender_id='sender_id')

        self.assertNotEqual(m1.id, m2.id)

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

    async def test_stream(self):
        listener = MessageQueueListenerMock()
        self.sut.register_listener(listener)
        self.sut.dispatch(listener_id=listener.id, msg=Message(msg_type='test'))

        num_dispatched = 0
        async for _ in self.sut.message_stream(listener):
            num_dispatched += 1

        self.assertEqual(0, num_dispatched)
        listener.start()

        async for _ in self.sut.message_stream(listener):
            num_dispatched += 1

        self.assertEqual(1, num_dispatched)


