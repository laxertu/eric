from logging import Logger
from unittest import TestCase
from unittest.mock import MagicMock

import pytest

import eric_sse.patterns
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.queues import Queue
from eric_sse.patterns import DeadLetterQueueHandler
from test.mock.channel import FakeChannel
from test.mock.connection import BrokenQueue

class DeadLetterQueueTestCase(TestCase):
    def setUp(self):
        self.dead_letter_queue = MagicMock(Queue)
        self.logger = MagicMock(Logger)

    def test_handle(self):
        channel = FakeChannel()
        sut = DeadLetterQueueHandler(self.dead_letter_queue)
        listener = MessageQueueListener()

        connection = Connection(listener=listener, queue=BrokenQueue())
        connection.register_queuing_error_handler(sut)
        channel.register_connection(connection)

        with pytest.raises(Exception) as e:
            message = Message("test")
            channel.broadcast(message)

        self.dead_letter_queue.push.assert_called_with(message)
