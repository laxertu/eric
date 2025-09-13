from unittest import TestCase
from unittest.mock import MagicMock

from eric_sse.connection import Connection, ConnectionsFactory
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ConnectionRepository, KvStorage
from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface
from eric_sse.repository import InMemoryStorage
from eric_sse.exception import ItemNotFound, InvalidChannelException

from test.mock.channel import FakeChannelRepository, FakeConnectionsFactory, FakeChannel


class TestInMemoryStorage(TestCase):

    def test_persistence(self):
        item1 = {'a': 1}
        sut = InMemoryStorage(items={'item1': item1})

        self.assertEqual(item1, sut.fetch_one('item1'))
        item2 = {'b': 2}
        sut.upsert('item2', item2)
        self.assertEqual(item2, sut.fetch_one('item2'))

        item3 = {'c': 3}
        sut.upsert('item1_1', item3)

        fetched_items = [i for i in sut.fetch_by_prefix('item1')]
        self.assertEqual([item1, item3], fetched_items)

        fetched_items = [i for i in sut.fetch_all()]
        self.assertEqual([item1, item2, item3], fetched_items)

        sut.delete('item1')
        with self.assertRaises(ItemNotFound):
            sut.fetch_one('item1')
        try:
            sut.delete('fake_key')
        except KeyError:
            self.fail('Delete on nonexistent key raised exception')


class ConnectionsRepositoryTestCase(TestCase):

    def setUp(self):
        self.listeners_repository = MagicMock(spec=ListenerRepositoryInterface)
        self.queues_repository = MagicMock(spec=QueueRepositoryInterface)
        self.connections_factory = MagicMock(spec=ConnectionsFactory)
        self.storage = MagicMock(spec=KvStorage)

        self.sut = ConnectionRepository(
            storage=self.storage,
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository,
            connections_factory=self.connections_factory
        )

    def test_persist_operations_are_delegated_to_composites(self):
        connection = Connection(
            listener=MessageQueueListener(),
            queue=InMemoryQueue(),
        )

        self.sut.persist(channel_id='fake_channel', connection=connection)
        self.listeners_repository.persist.assert_called_once_with(connection_id=connection.id, listener=connection.listener)
        self.queues_repository.persist.assert_called_once_with(connection_id=connection.id, queue=connection.queue)
        self.storage.upsert.assert_called()

    def test_deletions_are_delegated_to_composites(self):
        connection = Connection(
            listener=MessageQueueListener(),
            queue=InMemoryQueue(),
        )

        self.sut.persist(channel_id='fake_channel', connection=connection)
        self.sut.delete(connection_id=connection.id)

        self.listeners_repository.delete.assert_called_once_with(connection_id=connection.id)
        self.queues_repository.delete.assert_called_once_with(connection_id=connection.id)
        self.storage.delete.assert_called()


    def test_error_handling(self):
        self.sut = ConnectionRepository(
            storage=InMemoryStorage(),
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository,
            connections_factory=self.connections_factory
        )
        with self.assertRaises(ItemNotFound):
            self.sut.load_one('nonexistent_channel')



class AbstractChannelRepositoryInMemoryStorageIntegrationTestCase(TestCase):
    def setUp(self):
        self.listeners_repository = MagicMock(spec=ListenerRepositoryInterface)
        self.queues_repository = MagicMock(spec=QueueRepositoryInterface)
        self.connections_factory = FakeConnectionsFactory()


    def create_sut(self):
        connections_repository = ConnectionRepository(
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository,
            connections_factory=self.connections_factory,
            storage=InMemoryStorage(),
        )
        return FakeChannelRepository(
            storage=InMemoryStorage(),
            connections_repository=connections_repository
        )

    def test_persistence(self):
        sut = self.create_sut()
        channel = FakeChannel()
        sut.persist(channel=channel)

        channels = [c for c in sut.load_all()]
        self.assertEqual(len(channels), 1)

        self.assertEqual(channels[0].id, channel.id)
        self.assertEqual(sut.load_one(channel_id=channel.id).id, channel.id)

        sut.delete(channel_id=channel.id)
        channels = [c for c in sut.load_all()]
        self.assertEqual(len(channels), 0)
        # Test delete idempotency
        sut.delete(channel_id=channel.id)

    def test_missing_connections_are_deleted_on_persist(self):
        sut = self.create_sut()
        channel = FakeChannel()
        listener = channel.add_listener()
        connection_id = [c for c in channel.get_connections()][0].id
        sut.persist(channel=channel)
        channel.remove_listener(listener.id)
        sut.persist(channel=channel)

        self.listeners_repository.delete.assert_called_once_with(connection_id = connection_id)

        channel = sut.load_one(channel_id=channel.id)
        self.assertEqual(0, len([c for c in channel.get_connections()]))
"""
MessageQueueListenerMock



class FullPathTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.listeners_repository = MagicMock(spec=ListenerRepositoryInterface)
        self.queues_repository = MagicMock(spec=QueueRepositoryInterface)
        self.connections_factory = FakeConnectionsFactory()

    def create_sut(self):
        connections_repository = ConnectionRepository(
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository,
            connections_factory=self.connections_factory,
            storage=InMemoryStorage(),
        )
        return FakeChannelRepository(
            storage=InMemoryStorage(),
            connections_repository=connections_repository
        )
    async def test_one(self):
        sut = self.create_sut()
        channel = FakeChannel()


        listener = channel.add_listener()
        message = Message(msg_type='test')

        channel.dispatch(listener.id, message)
        channel.broadcast(message)

        sut.persist(channel=channel)
        channel_clone = sut.load_one(channel_id=channel.id)
        listener_clone = channel_clone.get_listener(listener.id)

        async for received_message in channel_clone.message_stream(listener_clone):
            self.assertEqual(received_message.msg_type, 'test')

"""