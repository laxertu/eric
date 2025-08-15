from dataclasses import dataclass

import eric_sse
from eric_sse.listener import MessageQueueListener, PersistableListener
from eric_sse.queues import Queue, PersistableQueue

class Connection:
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    def __init__(self, listener: MessageQueueListener, queue: Queue):
        self.listener = listener
        self.queue = queue
        self.id = eric_sse.generate_uuid()

class PersistableConnection(Connection):
    listener: PersistableListener
    queue: PersistableQueue
