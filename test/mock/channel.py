from typing import Any

from eric_sse.entities import AbstractChannel
from eric_sse.message import MessageContract


class FakeChannel(AbstractChannel):
    def adapt(self, msg: MessageContract) -> Any:
        return msg
