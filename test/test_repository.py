from unittest import TestCase
from unittest.mock import MagicMock
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ChannelRepository, ConnectionRepository, PrefixedStorage, KvListenerRepository, \
    KvQueueRepository
from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface

from eric_sse.repository import InMemoryStorage
from eric_sse.exception import ItemNotFound
from test.mock.channel import FakeChannel


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

        fetched_items = [i for i in sut.fetch_by_prefix('')]
        self.assertEqual([item1, item2, item3], fetched_items)

        sut.delete('item1')
        with self.assertRaises(ItemNotFound):
            sut.fetch_one('item1')
        try:
            sut.delete('fake_key')
        except KeyError:
            self.fail('Delete on nonexistent key raised exception')


class ChannelRepositoryInMemoryStorageIntegrationTestCase(TestCase):
    def setUp(self):
        self.listeners_repository = MagicMock(spec=ListenerRepositoryInterface)
        self.queues_repository = MagicMock(spec=QueueRepositoryInterface)
        self.listeners_repository.create.side_effect = MessageQueueListener
        self.queues_repository.create.side_effect = InMemoryQueue


    def create_sut(self):
        connections_repository = ConnectionRepository(
            listeners_repository=self.listeners_repository,
            queues_repository=self.queues_repository,
            storage=InMemoryStorage(),
        )
        return ChannelRepository(
            storage=InMemoryStorage(),
            connections_repository=connections_repository,
            channel_class=FakeChannel
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


class MyListener(MessageQueueListener):
    pass


class MyQueue(InMemoryQueue):
    pass


class PrefixedStorageTestCase(TestCase):

    def test_keys_are_namespaced(self):
        storage = InMemoryStorage()
        a = PrefixedStorage(storage, 'a:')
        b = PrefixedStorage(storage, 'b:')

        a.upsert('k', 1)
        b.upsert('k', 2)
        self.assertEqual({'a:k': 1, 'b:k': 2}, storage.items)
        self.assertEqual(1, a.fetch_one('k'))
        self.assertEqual([2], list(b.fetch_by_prefix('')))
        self.assertEqual([1], list(a.fetch_by_prefix('k')))

        a.delete('k')
        with self.assertRaises(ItemNotFound):
            a.fetch_one('k')
        self.assertEqual(2, b.fetch_one('k'))


class ConnectionRepositoryCreateTestCase(TestCase):

    def test_create(self):
        sut = ConnectionRepository(
            storage=InMemoryStorage(),
            listeners_repository=KvListenerRepository(InMemoryStorage(), listener_factory=MyListener),
            queues_repository=KvQueueRepository(InMemoryStorage(), queue_factory=MyQueue)
        )
        connection = sut.create()
        self.assertIsInstance(connection.listener, MyListener)
        self.assertIsInstance(connection.queue, MyQueue)

        listener = MyListener()
        self.assertIs(listener, sut.create(listener=listener).listener)
        self.assertIsNot(sut.create().queue, sut.create().queue)

        # Creating is not persisting
        self.assertEqual([], list(sut.load_all('any')))


class ConnectionRepositoryPrefixTestCase(TestCase):

    def test_channel_ids_sharing_a_prefix_do_not_mix(self):
        storage = InMemoryStorage()
        sut = ConnectionRepository(
            storage=storage,
            listeners_repository=KvListenerRepository(InMemoryStorage()),
            queues_repository=KvQueueRepository(InMemoryStorage())
        )
        sut.persist('a', sut.create())
        sut.persist('ab', sut.create())

        self.assertEqual(1, len(list(sut.load_all('a'))))
