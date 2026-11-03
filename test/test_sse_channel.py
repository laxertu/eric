from unittest import TestCase

from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import ReliableMessage


class SSEChannelAdaptTestCase(TestCase):

    def test_message_without_id(self):
        channel = SSEChannel(retry_timeout_milliseconds=10)

        self.assertEqual(
            {'event': 'test', 'retry': 10, 'data': 'hello'},
            channel.adapt(Message(msg_type='test', msg_payload='hello'))
        )

    def test_message_with_id(self):
        channel = SSEChannel(retry_timeout_milliseconds=10)

        for msg in (
                Message(msg_type='test', msg_payload='hello', msg_id='m1'),
                ReliableMessage('m1', Message(msg_type='test', msg_payload='hello')),
        ):
            self.assertEqual(
                {'event': 'test', 'retry': 10, 'data': 'hello', 'id': 'm1'},
                channel.adapt(msg)
            )
