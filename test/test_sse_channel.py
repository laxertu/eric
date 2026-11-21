import json
from unittest import TestCase

from eric_sse.exception import InvalidConnectionException, InternalStreamError

from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel, DataProcessingChannel
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


class AdaptErrorTestCase(TestCase):

    def test_sse_channel(self):
        channel = SSEChannel(retry_timeout_milliseconds=10)

        event = channel.adapt_error(InvalidConnectionException('listener gone'))

        self.assertEqual(
            {'event': 'error', 'retry': 10, 'data': {'error': 'InvalidConnectionException', 'message': 'listener gone'}},
            event
        )
        json.dumps(event)

    def test_data_processing_channel(self):
        self.assertEqual(
            {'event': 'error', 'data': {'error': 'InternalStreamError', 'message': 'Internal error'}},
            DataProcessingChannel(max_workers=1).adapt_error(InternalStreamError())
        )
