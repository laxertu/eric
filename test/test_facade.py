from unittest import TestCase

from eric_sse.connection import DefaultConnectionsFactory
from eric_sse.exception import ItemNotFound
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import InMemoryStorage, PrefixedStorage, ConnectionRepository, KvListenerRepository, \
    KvQueueRepository
from eric_sse.facade import Facade


class MyListener(MessageQueueListener):
    pass


class MyQueue(InMemoryQueue):
    pass


class FacadeTestCase(TestCase):

    def setUp(self):
        self.storage = InMemoryStorage()
        self.sut = Facade(storage=self.storage, listener_class=MyListener, queue_factory=MyQueue)

    def test_create_and_get_channel(self):
        channel = self.sut.create_channel(retry_timeout_milliseconds=42)
        loaded = self.sut.get_channel(channel.id)
        self.assertIsInstance(loaded, SSEChannel)
        self.assertEqual(42, loaded.retry_timeout_milliseconds)
        self.assertEqual([channel.id], [c.id for c in self.sut.get_channels()])

    def test_add_listener_uses_configured_classes(self):
        channel = self.sut.create_channel()
        listener = self.sut.add_listener(channel.id)
        self.assertIsInstance(listener, MyListener)

        connections = list(self.sut.get_channel(channel.id).get_connections())
        self.assertEqual([listener.id], [c.listener.id for c in connections])
        self.assertIsInstance(connections[0].queue, MyQueue)

    def test_queued_messages_survive_reload(self):
        channel = self.sut.create_channel()
        listener = self.sut.add_listener(channel.id)
        channel = self.sut.get_channel(channel.id)
        channel.dispatch(listener.id, Message(msg_type='test', msg_payload='hi'))
        self.sut.repository.persist(channel)

        loaded = Facade(storage=self.storage).get_channel(channel.id)
        loaded.get_listener(listener.id).start()
        self.assertEqual('hi', loaded.deliver_next(listener.id).payload)

    def test_remove_listener(self):
        channel = self.sut.create_channel()
        listener_1 = self.sut.add_listener(channel.id)
        listener_2 = self.sut.add_listener(channel.id)

        self.sut.remove_listener(channel.id, listener_1.id)
        connections = list(self.sut.get_channel(channel.id).get_connections())
        self.assertEqual([listener_2.id], [c.listener.id for c in connections])

    def test_delete_channel_leaves_storage_empty(self):
        channel = self.sut.create_channel()
        self.sut.add_listener(channel.id)
        self.sut.add_listener(channel.id)

        self.sut.delete_channel(channel.id)
        self.assertEqual({}, self.storage.items)

    def test_namespaces_share_one_storage(self):
        channel = self.sut.create_channel()
        self.sut.add_listener(channel.id)
        prefixes = {k.split(':')[0] for k in self.storage.items}
        self.assertEqual({'channel', 'connection', 'listener', 'queue'}, prefixes)

    def test_custom_queue_repository_class(self):
        deleted = []

        class MyQueueRepository(KvQueueRepository):
            def delete(self, connection_id: str):
                deleted.append(connection_id)
                super().delete(connection_id)

        sut = Facade(storage=InMemoryStorage(), queue_repository_class=MyQueueRepository)
        channel = sut.create_channel()
        sut.add_listener(channel.id)
        connection = next(iter(sut.get_channel(channel.id).get_connections()))

        sut.delete_channel(channel.id)
        self.assertEqual([connection.id], deleted)


class PrefixedStorageTestCase(TestCase):

    def test_keys_are_namespaced(self):
        storage = InMemoryStorage()
        a = PrefixedStorage(storage, 'a:')
        b = PrefixedStorage(storage, 'b:')

        a.upsert('k', 1)
        b.upsert('k', 2)
        self.assertEqual({'a:k': 1, 'b:k': 2}, storage.items)
        self.assertEqual(1, a.fetch_one('k'))
        self.assertEqual([2], list(b.fetch_all()))
        self.assertEqual([1], list(a.fetch_by_prefix('k')))

        a.delete('k')
        with self.assertRaises(ItemNotFound):
            a.fetch_one('k')
        self.assertEqual(2, b.fetch_one('k'))


class DefaultConnectionsFactoryTestCase(TestCase):

    def test_create(self):
        sut = DefaultConnectionsFactory(listener_class=MyListener, queue_factory=MyQueue)
        connection = sut.create()
        self.assertIsInstance(connection.listener, MyListener)
        self.assertIsInstance(connection.queue, MyQueue)

        listener = MyListener()
        self.assertIs(listener, sut.create(listener=listener).listener)
        self.assertIsNot(sut.create().queue, sut.create().queue)


class ConnectionRepositoryPrefixTestCase(TestCase):

    def test_channel_ids_sharing_a_prefix_do_not_mix(self):
        storage = InMemoryStorage()
        sut = ConnectionRepository(
            storage=storage,
            listeners_repository=KvListenerRepository(InMemoryStorage()),
            queues_repository=KvQueueRepository(InMemoryStorage())
        )
        factory = DefaultConnectionsFactory()
        sut.persist('a', factory.create())
        sut.persist('ab', factory.create())

        self.assertEqual(1, len(list(sut.load_all('a'))))
