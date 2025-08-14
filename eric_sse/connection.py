from dataclasses import dataclass

import eric_sse
from eric_sse.listener import MessageQueueListener, PersistableListener
from eric_sse.queues import Queue, PersistableQueue

@dataclass
class Connection:
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    listener: MessageQueueListener
    queue: Queue
    id: str = eric_sse.generate_uuid()


class PersistableConnection(Connection):
    listener: PersistableListener
    queue: PersistableQueue
