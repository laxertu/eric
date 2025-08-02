from dataclasses import dataclass

from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue


@dataclass
class Connection:
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    listener: MessageQueueListener
    queue: Queue
