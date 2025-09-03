from typing import Any
from unittest import TestCase

from eric_sse.entities import AbstractChannel
from eric_sse.exception import InvalidListenerException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, SignedMessage, UniqueMessage, MessageContract
from eric_sse.connection import Connection, InMemoryConnectionsFactory
from eric_sse.queues import InMemoryQueue
from eric_sse.prefabs import SSEChannel


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

    def test_listeners_management(self):

        class _FakeChannel(AbstractChannel):
            def adapt(self, msg: MessageContract) -> Any:
                return msg

        fake_channel = _FakeChannel()
        listener = fake_channel.add_listener()
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


