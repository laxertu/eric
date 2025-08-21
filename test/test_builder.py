from unittest import TestCase
from unittest.mock import MagicMock

from eric_sse.inmemory import InMemoryChannelRepository, InMemoryConnectionRepository
from eric_sse.builder import ChannelBuilder
from eric_sse.prefabs import SSEChannel

class TestBuilder(TestCase):
    def test_channels_are_loaded(self):

        channels_repository = InMemoryChannelRepository()
        channel = SSEChannel()
        _ = channel.add_listener()
        channels_repository.persist(channel)
        connection__repository_mock = MagicMock(InMemoryConnectionRepository)

        sut =  ChannelBuilder(
            channel_repository=channels_repository,
            connection_repository=connection__repository_mock
        )
        _ = sut.build_one(channel.id)
        connection__repository_mock.load_all.assert_called()
