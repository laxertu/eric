from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import StoppedListenerException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import DataProcessingChannel
from eric_sse.queues import InMemoryQueue
from test.mock.failures import RecordingListenerErrorHandler, RecordingQueuingErrorHandler


class FailingOnTypeListener(MessageQueueListener):
    """Fails processing messages of type 'bad'."""
    def on_message(self, msg: MessageContract) -> None:
        if msg.type == 'bad':
            raise RuntimeError('on_message failed')


class FailingAfterTwoPopsQueue(InMemoryQueue):
    def __init__(self):
        super().__init__()
        self.pops = 0

    def pop(self, timeout: float = 0) -> MessageContract:
        self.pops += 1
        if self.pops > 2:
            raise RuntimeError('pop failed')
        return super().pop(timeout)


class DataProcessingChannelTestCase(IsolatedAsyncioTestCase):

    def setUp(self):
        self.queuing_handler = RecordingQueuingErrorHandler()
        self.listener_handler = RecordingListenerErrorHandler()
        self.builder = (
            ChannelRepositoryBuilder(DataProcessingChannel)
            .listeners(FailingOnTypeListener)
            .queuing_error_handler(self.queuing_handler)
            .listener_error_handler(self.listener_handler)
        )

    def create_channel(self) -> DataProcessingChannel:
        return self.builder.build().create({'max_workers': 2})

    @staticmethod
    async def process(channel: DataProcessingChannel, connection_id: str) -> list[str]:
        return sorted([event['event'] async for event in channel.process_queue(connection_id)])

    async def test_processes_every_queued_message(self):
        channel = self.create_channel()
        connection = channel.add_connection()
        for i in range(3):
            channel.dispatch(connection.id, Message(msg_type=f'test{i}'))
        connection.listener.start()

        self.assertEqual(['test0', 'test1', 'test2'], await self.process(channel, connection.id))

    async def test_a_stopped_listener_can_not_be_processed(self):
        channel = self.create_channel()
        connection = channel.add_connection()
        channel.dispatch(connection.id, Message(msg_type='test'))

        with self.assertRaises(StoppedListenerException):
            await self.process(channel, connection.id)

    async def test_listener_errors_are_handled_and_processing_goes_on(self):
        channel = self.create_channel()
        connection = channel.add_connection()
        for msg_type in ('good', 'bad', 'other'):
            channel.dispatch(connection.id, Message(msg_type=msg_type))
        connection.listener.start()

        self.assertEqual(['bad', 'good', 'other'], await self.process(channel, connection.id))
        self.assertEqual([('on_message', connection.id, 'bad', 'on_message failed')], self.listener_handler.events)

    async def test_queue_errors_are_handled_and_raised_after_popped_messages(self):
        channel = self.builder.queues(FailingAfterTwoPopsQueue).build().create({'max_workers': 2})
        connection = channel.add_connection()
        for i in range(3):
            channel.dispatch(connection.id, Message(msg_type=f'test{i}'))
        connection.listener.start()

        processed = []
        with self.assertRaises(RuntimeError):
            async for event in channel.process_queue(connection.id):
                processed.append(event['event'])

        self.assertEqual(['test0', 'test1'], sorted(processed))
        self.assertEqual([('pop', connection.id, 'pop failed')], self.queuing_handler.events)
