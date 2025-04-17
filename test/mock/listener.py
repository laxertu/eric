from eric_sse.entities import MessageQueueListener
from eric_sse.message import Message


class MessageQueueListenerMock(MessageQueueListener):

    def __init__(self, num_messages_before_disconnect=1, fixtures: dict[int, Message] = None):
        super().__init__()
        self.disconnect_after = num_messages_before_disconnect
        self.num_received = 0
        self.fixtures = fixtures

    def on_message(self, msg: Message) -> None:
        self.num_received += 1

        if self.fixtures is not None:
            assert msg.type == self.fixtures[self.num_received].type
            assert msg.payload == self.fixtures[self.num_received].payload

        if self.num_received >= self.disconnect_after:
            self.stop_sync()
