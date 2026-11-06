from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.prefabs import SSEChannel
from eric_sse.repository import InMemoryStorage
from test.repository_contract import ChannelRepositoryContract


class InMemoryStorageTestCase(ChannelRepositoryContract, TestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel, InMemoryStorage())

    def channel_data(self) -> dict:
        return {'stream_delay_seconds': 1, 'retry_timeout_milliseconds': 10}
