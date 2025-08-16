import eric_sse
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue

class Connection:
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    def __init__(self, listener: MessageQueueListener, queue: Queue, connection_id: str | None = None):
        self.listener = listener
        self.queue = queue
        self.id = connection_id or eric_sse.generate_uuid()
