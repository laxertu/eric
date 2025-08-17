from dataclasses import dataclass

import eric_sse
from eric_sse.listener import PersistableListener
from eric_sse.queues import PersistableQueue
from eric_sse.channel import ObjectAsKeyValuePersistenceMixin

class Connection(ObjectAsKeyValuePersistenceMixin):
    """
    A connection is just a listener and its related message queue

    :param ~eric_sse.listener.MessageQueueListener listener:
    :param ~eric_sse.queues.Queue queue:
    """
    def __init__(self, listener: PersistableListener, queue: PersistableQueue, connection_id: str | None = None):
        self.listener = listener
        self.queue = queue
        self.id = connection_id or eric_sse.generate_uuid()

    @property
    def kv_key(self) -> str:
        return self.id

    @property
    def kv_setup_values_as_dict(self) -> dict:
        return {}

    def kv_setup_by_dict(self, setup: dict):
        pass

    @property
    def kv_constructor_params_as_dict(self) -> dict:
        return {
            'connection_id': self.id,
            'listener': self.listener.kv_as_dict,
            'queue': self.queue.kv_as_dict,
        }
