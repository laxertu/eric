from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from eric_sse.handlers import ListenerErrorHandler, QueuingErrorHandler
from eric_sse.message import Message
from test.mock.channel import FakeChannel
from test.mock.connection import BrokenListener, BrokenQueue, BrokenConnectionFactory


class ErrorsHandlingTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.listeners_handler_mock = MagicMock(ListenerErrorHandler)
        self.listeners_handler_mock2 = MagicMock(ListenerErrorHandler)
        self.queues_handler_mock = MagicMock(QueuingErrorHandler)
        self.queues_handler_mock2 = MagicMock(QueuingErrorHandler)


    def test_queues_handler(self):

        # Set up broken push
        channel = FakeChannel(
            connections_factory=BrokenConnectionFactory(
                q_handlers=[self.queues_handler_mock, self.queues_handler_mock2],
                queue=self.queues_handler_mock
            )
        )

        my_listener = BrokenListener()
        channel.register_listener(my_listener)
        my_listener.start()

        # act
        msg = Message(msg_type='test')
        with self.assertRaises(Exception) as context:
            channel.dispatch(listener_id=my_listener.id, msg=msg)
        self.queues_handler_mock.handle_push_error.assert_called_once_with(msg=msg, exception=context.exception)


        # Set up broken pop
        channel = FakeChannel(
            connections_factory=BrokenConnectionFactory(
                q_handlers=[
                    self.queues_handler_mock,
                    self.queues_handler_mock2,
                ],
                queue=BrokenQueue(broken_push=False),
            )
        )
        my_listener = BrokenListener()
        channel.register_listener(my_listener)
        my_listener.start()

        with self.assertRaises(Exception) as context:
            channel.dispatch(listener_id=my_listener.id, msg=Message(msg_type='test'))
            channel.deliver_next(listener_id=my_listener.id)
        self.queues_handler_mock.handle_pop_error.assert_called_once_with(exception=context.exception)
        self.queues_handler_mock2.handle_pop_error.assert_called_once_with(exception=context.exception)


    def test_listeners_handler(self):
        channel = FakeChannel()
        channel.register_listener_error_handler(self.listeners_handler_mock)
        my_listener = BrokenListener()
        my_listener.start()
        channel.register_listener(my_listener)
        msg = Message(msg_type='test')
        failed: bool = False
        try:
            channel.dispatch(listener_id=my_listener.id, msg=msg)
            channel.deliver_next(listener_id=my_listener.id)
        except Exception as e:
            failed = True
            self.listeners_handler_mock.handle_on_message_error.assert_called_once_with(msg=msg, exception=e)

        if not failed:
            self.fail('Exception was not raised')

