from typing import Any

from eric_sse.entities import AbstractChannel
from eric_sse.message import MessageContract
from eric_sse.repository import AbstractChannelRepository

class FakeChannel(AbstractChannel):
    def adapt(self, msg: MessageContract) -> Any:
        return msg

class FakeChannelRepository(AbstractChannelRepository):

    @staticmethod
    def _channel_to_dict(channel: AbstractChannel) -> dict:
        return {'channel_id': channel.id}

    def create(self, channel_data: dict) -> FakeChannel:
        return FakeChannel(**channel_data, connections_factory=self.connections_repository)
