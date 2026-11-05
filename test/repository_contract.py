from abc import ABC, abstractmethod
from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import ItemNotFound
from eric_sse.message import Message


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

    def test_persisted_connection_parts_are_returned_by_their_repositories(self: 'ChannelRepositoryContract | TestCase'):
        connections_repository = self.create_builder().build().connections_repository
        connection = connections_repository.create()
        connection.queue.push(Message(msg_type='greeting', msg_payload='hello'))

        connections_repository.persist(channel_id='channel', connection=connection)

        self.assertEqual(connection.id, connections_repository.load_one('channel', connection.id).id)
        self.assertEqual(connection.listener.id, connections_repository.listeners_repository.load(connection.id).id)
        message = connections_repository.queues_repository.load(connection.id).pop()
        self.assertEqual(('greeting', 'hello'), (message.type, message.payload))

    def test_connections_removed_from_a_channel_are_deleted_on_persist(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel = sut.create({})
        kept = channel.add_listener()
        removed = channel.add_listener()
        connection_ids = {connection.listener.id: connection.id for connection in channel.get_connections()}
        sut.persist(channel)

        channel.remove_listener(removed.id)
        sut.persist(channel)

        loaded_listener_ids = [connection.listener.id for connection in sut.load_one(channel.id).get_connections()]
        self.assertEqual([kept.id], loaded_listener_ids)
        connections_repository = sut.connections_repository
        removed_connection_id = connection_ids[removed.id]
        with self.assertRaises(ItemNotFound):
            connections_repository.listeners_repository.load(removed_connection_id)
        with self.assertRaises(ItemNotFound):
            connections_repository.queues_repository.load(removed_connection_id)
