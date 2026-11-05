from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.repository import InMemoryStorage
from test.mock.channel import FakeChannel
from test.repository_contract import ChannelRepositoryContract


class InMemoryStorageTestCase(ChannelRepositoryContract, TestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(FakeChannel, InMemoryStorage())

    def channel_data(self) -> dict:
        return {}
