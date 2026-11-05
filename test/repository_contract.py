from abc import ABC, abstractmethod
from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import ItemNotFound


class ChannelRepositoryContract(ABC):
    """
    Use cases every channel repository has to satisfy, whatever its storages or custom repositories.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder`: to check a custom part, subclass this
    together with ``TestCase`` and return a builder configured with it::

        class RedisStorageTestCase(ChannelRepositoryContract, TestCase):
            def create_builder(self):
                return ChannelRepositoryBuilder(FakeChannel, RedisStorage())

    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self) -> ChannelRepositoryBuilder:
        """Returns the builder under test. Called once per test."""
        pass

    def test_deleting_a_channel_deletes_all_its_connections(self: 'ChannelRepositoryContract | TestCase'):
        # KvStorage.fetch_by_prefix: implementations must tolerate deletions of fetched keys while the result is
        # being iterated. ChannelRepository.delete relies on it to delete connections one by one.
        sut = self.create_builder().build()
        channel = sut.create({})
        for _ in range(3):
            channel.add_listener()
        connection_ids = [connection.id for connection in channel.get_connections()]
        sut.persist(channel)

        sut.delete(channel.id)

        with self.assertRaises(ItemNotFound):
            sut.load_one(channel.id)
        connections_repository = sut.connections_repository
        self.assertEqual([], list(connections_repository.load_ids(channel_id=channel.id)))
        for connection_id in connection_ids:
            with self.assertRaises(ItemNotFound):
                connections_repository.listeners_repository.load(connection_id)
            with self.assertRaises(ItemNotFound):
                connections_repository.queues_repository.load(connection_id)

    def test_all_channels_can_be_deleted_while_loading_them(self: 'ChannelRepositoryContract | TestCase'):
        # KvStorage.fetch_by_prefix: implementations must tolerate deletions of fetched keys while the result is
        # being iterated. ChannelRepository.load_all yields channels while iterating it.
        sut = self.create_builder().build()
        channel_ids = []
        for _ in range(3):
            channel = sut.create({})
            sut.persist(channel)
            channel_ids.append(channel.id)

        deleted_ids = []
        for channel in sut.load_all():
            sut.delete(channel.id)
            deleted_ids.append(channel.id)

        self.assertCountEqual(channel_ids, deleted_ids)
        self.assertEqual([], list(sut.load_all()))
