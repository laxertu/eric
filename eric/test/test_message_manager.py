from unittest import TestCase
from pytest import raises
from eric import (Eric, InvalidSessionException, Message, InvalidListenerException,
                          MessageQueueListener)


class MessageManagerTestCase(TestCase):

    def setUp(self):
        Eric.QUEUES = {}
        self.sut = Eric()

    def test_register_session(self):

        sut = Eric()
        sut.register_session('1')
        self.assertEqual(1, len(sut.QUEUES))


    def test_no_session(self):
        with raises(InvalidSessionException):
            self.sut.add(session_id='unexistent', listener_id='unexistent', msg=Message(type='test'))

    def test_no_listener(self):
        sut = self.sut

        with raises(InvalidListenerException):
            sut.register_session(session_id='1')
            sut.add(session_id='1', listener_id='unexistent', msg=Message(type='test'))

    def test_broadcast_no_listeners(self):
        sut = self.sut
        sut.register_session('1')
        sut.broadcast(session_id='1', msg=Message(type= 'test'))
        self.assertEqual({'1': {}}, sut.QUEUES)

    def test_broadcast_ok(self):

        sut = self.sut
        sut.register_session('sessionid')
        watcher1_listener = MessageQueueListener()
        watcher2_listener = MessageQueueListener()
        msg_to_send = Message(type= 'test', payload={})

        sut.add_listener('sessionid', watcher1_listener)
        sut.add_listener('sessionid', watcher2_listener)

        # 1 broadcast
        sut.broadcast(session_id='sessionid', msg=msg_to_send)
        expected = {
            'sessionid': {
                watcher1_listener.id: [msg_to_send],
                watcher2_listener.id: [msg_to_send]
            }
        }
        self.assertEqual(expected, sut.QUEUES)

        # message is received correctly
        msg_received = sut.get('sessionid', watcher1_listener.id)
        self.assertEqual(msg_to_send, msg_received)

        # queue is ok
        expected = {
            'sessionid': {
                watcher1_listener.id: [],
                watcher2_listener.id: [msg_to_send]
            }
        }
        self.assertEqual(expected, sut.QUEUES)


