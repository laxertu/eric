"""Test doubles used by contracts, e.g. parts that always fail and error handlers recording what they handle."""
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract
from eric_sse.queues import InMemoryQueue


class BrokenQueue(InMemoryQueue):
    def push(self, message: MessageContract) -> None:
        raise RuntimeError('push failed')

    def pop(self, timeout: float = 0) -> MessageContract:
        raise RuntimeError('pop failed')

    async def wait_pop(self, timeout: float) -> MessageContract:
        raise RuntimeError('wait_pop failed')


class BrokenListener(MessageQueueListener):
    def on_message(self, msg: MessageContract) -> None:
        raise RuntimeError('on_message failed')


class RecordingQueuingErrorHandler(QueuingErrorHandler):
    def __init__(self):
        self.events = []

    def handle_push_error(self, connection_id: str, msg: MessageContract, exception: Exception):
        self.events.append(('push', connection_id, msg.type, str(exception)))

    def handle_pop_error(self, connection_id: str, exception: Exception):
        self.events.append(('pop', connection_id, str(exception)))


class RecordingListenerErrorHandler(ListenerErrorHandler):
    def __init__(self):
        self.events = []

    def handle_on_message_error(self, connection_id: str, msg: MessageContract, exception: Exception):
        self.events.append(('on_message', connection_id, msg.type, str(exception)))
