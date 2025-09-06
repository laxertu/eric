from unittest import TestCase
from unittest.mock import MagicMock
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ConnectionRepository, KvStorage
from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface

from eric_sse.repository import InMemoryStorage
from eric_sse.exception import ItemNotFound


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

class ConnectionsRepositoryTestCase(TestCase):

    def setUp(self):
        self.listeners_repository = MagicMock(spec=ListenerRepositoryInterface)
        self.queues_repository = MagicMock(spec=QueueRepositoryInterface)
        self.storage = MagicMock(spec=KvStorage)

        self.sut = ConnectionRepository(
            storage=self.storage,
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository
        )

    def test_persist_operations_are_delegated_to_composites(self):
        connection = Connection(
            listener=MessageQueueListener(),
            queue=InMemoryQueue(),
        )

        self.sut.persist(channel_id='fake_channel', connection=connection)
        self.listeners_repository.persist.assert_called_once_with(connection_id=connection.id, listener=connection.listener)
        self.queues_repository.persist.assert_called_once_with(connection_id=connection.id, queue=connection.queue)
        self.storage.upsert.assert_called_once()

    def test_deletions_are_delegated_to_composites(self):
        connection = Connection(
            listener=MessageQueueListener(),
            queue=InMemoryQueue(),
        )

        self.sut.persist(channel_id='fake_channel', connection=connection)
        self.sut.delete(channel_id='fake_channel', connection_id=connection.id)

        self.listeners_repository.delete.assert_called_once_with(connection_id=connection.id)
        self.queues_repository.delete.assert_called_once_with(connection_id=connection.id)
        self.storage.delete.assert_called_once()


    def error_handling(self):
        with self.assertRaises(ItemNotFound):
            self.sut.load_one('nonexistent_channel', 'nonexistent_connection')


