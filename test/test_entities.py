from unittest import TestCase
from eric_sse.message import Message, SignedMessage, UniqueMessage


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
