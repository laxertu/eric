from eric_sse.connection import ConnectionsFactory, Connection
from eric_sse.handlers import QueuingErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract, Message
from eric_sse.queues import Queue


class BrokenListener(MessageQueueListener):

    def on_message(self, msg: MessageContract) -> None:
        raise Exception()


class BrokenQueue(Queue):
    def __init__(self, broken_push: bool = True, broken_pop: bool = True) -> None:
        self.broken_push = broken_push
        self.broken_pop = broken_pop

    def pop(self) -> MessageContract:
        if self.broken_pop:
            raise Exception()
        return Message(msg_type='test')

    def push(self, message: MessageContract) -> None:
        if self.broken_push:
            raise Exception()


class BrokenConnectionFactory(ConnectionsFactory):

    def __init__(
            self,
            q_handlers: list[QueuingErrorHandler],
            queue: Queue | None = None,
    ):
        self.q_handlers = q_handlers
        self.queue = queue or BrokenQueue()


    def create(self, listener: MessageQueueListener | None = None) -> Connection:
        connection = Connection(listener=listener, queue=self.queue)
        for handler in self.q_handlers:
            connection.register_queuing_error_handler(handler)
        return connection
