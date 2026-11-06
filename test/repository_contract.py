from abc import ABC, abstractmethod
from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.entities import AbstractChannel
from eric_sse.exception import ItemNotFound, NoMessagesException
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.repository import ChannelRepository


class ChannelRepositoryContract(ABC):
    """
    Use cases every channel repository has to satisfy, whatever its storages or custom repositories.

    The fixture is a :class:`~eric_sse.builder.ChannelRepositoryBuilder`: to check a custom part, subclass this
    together with ``TestCase`` and return a builder configured with it::

        class RedisStorageTestCase(ChannelRepositoryContract, TestCase):
            def create_builder(self):
                return ChannelRepositoryBuilder(SSEChannel, RedisStorage())

            def channel_data(self):
                return {'retry_timeout_milliseconds': 10}

    Not a ``TestCase`` itself, so the abstract class is not collected.
    """

    @abstractmethod
    def create_builder(self) -> ChannelRepositoryBuilder:
        """Returns the builder under test. Called once per test."""
        pass

    @abstractmethod
    def channel_data(self) -> dict:
        """
        Returns the data passed to the built repository's ``create`` to create a channel of the builder's
        channel class. Without ``channel_id``: tests that need a given id add it, the other ones need generated ids,
        so that each call creates a different channel.
        """
        pass

    def _create_channel(self, sut: ChannelRepository, channel_id: str | None = None) -> AbstractChannel:
        data = self.channel_data()
        if channel_id is not None:
            data = {**data, 'channel_id': channel_id}
        return sut.create(data)

    def test_deleting_a_channel_deletes_all_its_connections(self: 'ChannelRepositoryContract | TestCase'):
        # KvStorage.fetch_by_prefix: implementations must tolerate deletions of fetched keys while the result is
        # being iterated. ChannelRepository.delete relies on it to delete connections one by one.
        sut = self.create_builder().build()
        channel = self._create_channel(sut)
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
        channel = self._create_channel(sut)
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

    def test_persisted_channels_are_returned_by_load_all_and_load_one(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel_ids = []
        for _ in range(2):
            channel = self._create_channel(sut)
            sut.persist(channel)
            channel_ids.append(channel.id)

        self.assertCountEqual(channel_ids, [channel.id for channel in sut.load_all()])
        for channel_id in channel_ids:
            self.assertEqual(channel_id, sut.load_one(channel_id).id)

    def test_channel_configuration_is_returned_after_reload(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel = self._create_channel(sut)
        sut.persist(channel)

        loaded = sut.load_one(channel.id).to_dict()

        self.assertEqual(channel.to_dict(), loaded)
        self.assertEqual(self.channel_data(), {key: loaded[key] for key in self.channel_data()})

    def test_deleting_a_channel_twice_does_not_fail(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel = self._create_channel(sut)
        sut.persist(channel)

        sut.delete(channel.id)
        sut.delete(channel.id)

        self.assertEqual([], list(sut.load_all()))

    def test_registered_listeners_are_returned_after_reload(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel = self._create_channel(sut)
        listener = MessageQueueListener()
        channel.register_listener(listener)
        sut.persist(channel)

        loaded = sut.load_one(channel.id)

        self.assertEqual([listener.id], [connection.listener.id for connection in loaded.get_connections()])

    def test_messages_are_kept_per_listener(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        channel = self._create_channel(sut)
        recipient = channel.add_listener()
        other = channel.add_listener()
        channel.dispatch(recipient.id, Message(msg_type='greeting', msg_payload='hello'))
        sut.persist(channel)

        queues = {connection.listener.id: connection.queue for connection in sut.load_one(channel.id).get_connections()}

        self.assertEqual('hello', queues[recipient.id].pop().payload)
        with self.assertRaises(NoMessagesException):
            queues[other.id].pop()

    def test_channels_whose_ids_share_a_prefix_do_not_mix(self: 'ChannelRepositoryContract | TestCase'):
        sut = self.create_builder().build()
        a = self._create_channel(sut, channel_id='a')
        a_listener = a.add_listener()
        ab = self._create_channel(sut, channel_id='ab')
        ab_listener = ab.add_listener()
        sut.persist(a)
        sut.persist(ab)

        self.assertEqual([a_listener.id], [connection.listener.id for connection in sut.load_one('a').get_connections()])

        sut.delete('a')

        self.assertEqual([ab_listener.id], [connection.listener.id for connection in sut.load_one('ab').get_connections()])
