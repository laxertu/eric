from abc import ABC

from eric_sse.entities import AbstractChannel
from eric_sse.persistence import ObjectAsKeyValuePersistenceMixin


class PersistableChannel(AbstractChannel, ObjectAsKeyValuePersistenceMixin, ABC):
    pass
