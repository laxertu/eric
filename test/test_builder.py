from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import ItemNotFound
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ChannelRepository, InMemoryStorage, KvListenerRepository, KvQueueRepository
from test.mock.channel import FakeChannel


class MyListener(MessageQueueListener):
    pass


class MyQueue(InMemoryQueue):
    pass


class ChannelRepositoryBuilderTestCase(TestCase):

    def test_defaults(self):
        sut = ChannelRepositoryBuilder(SSEChannel).build()
        self.assertIsInstance(sut, ChannelRepository)
        self.assertIs(SSEChannel, sut.channel_class)

        channel = sut.create({'retry_timeout_milliseconds': 42})
        self.assertIsInstance(channel, SSEChannel)
        connection = channel.add_connection()
        sut.persist(channel)

        loaded = sut.load_one(channel.id)
        self.assertEqual(42, loaded.retry_timeout_milliseconds)
        self.assertIsInstance(loaded.get_connection(connection.id).listener, MessageQueueListener)
        self.assertIsInstance(next(iter(loaded.get_connections())).queue, InMemoryQueue)

    def test_storage_layout(self):
        storage = InMemoryStorage()
        sut = ChannelRepositoryBuilder(SSEChannel, storage).build()
        channel = sut.create({})
        channel.add_connection()
        sut.persist(channel)
        connection = next(iter(channel.get_connections()))

        self.assertEqual(
            {
                f'channel:{channel.id}',
                f'connection:{channel.id}:{connection.id}',
                f'listener:{connection.id}',
                f'queue:{connection.id}',
            },
            set(storage.items)
        )

        sut.delete(channel.id)
        self.assertEqual({}, storage.items)

    def test_create_does_not_persist(self):
        storage = InMemoryStorage()
        sut = ChannelRepositoryBuilder(SSEChannel, storage).build()
        sut.create({}).add_connection()
        self.assertEqual({}, storage.items)

    def test_listener_and_queue_classes(self):
        sut = ChannelRepositoryBuilder(SSEChannel).listeners(MyListener).queues(MyQueue).build()

        channel = sut.create({})
        self.assertIsInstance(channel.add_connection().listener, MyListener)
        sut.persist(channel)

        loaded = sut.load_one(channel.id)
        self.assertIsInstance(loaded.add_connection().listener, MyListener)
        for connection in loaded.get_connections():
            self.assertIsInstance(connection.listener, MyListener)
            self.assertIsInstance(connection.queue, MyQueue)

    def test_custom_repositories(self):
        deleted = []

        class MyQueueRepository(KvQueueRepository):
            def delete(self, connection_id: str):
                deleted.append(connection_id)
                super().delete(connection_id)

        sut = (
            ChannelRepositoryBuilder(SSEChannel)
            .listeners_repository(KvListenerRepository(InMemoryStorage(), listener_factory=MyListener))
            .queues_repository(MyQueueRepository(InMemoryStorage(), queue_factory=MyQueue))
            .build()
        )
        channel = sut.create({})
        self.assertIsInstance(channel.add_connection().listener, MyListener)
        connection = next(iter(channel.get_connections()))
        self.assertIsInstance(connection.queue, MyQueue)
        sut.persist(channel)

        sut.delete(channel.id)
        self.assertEqual([connection.id], deleted)

    def test_dedicated_storages(self):
        default, channels, connections, listeners, queues = (InMemoryStorage() for _ in range(5))
        sut = (
            ChannelRepositoryBuilder(SSEChannel, default)
            .channels(channels)
            .connections(connections)
            .listeners(storage=listeners)
            .queues(storage=queues)
            .build()
        )
        channel = sut.create({})
        channel.add_connection()
        sut.persist(channel)

        self.assertEqual({}, default.items)
        for storage, namespace in ((channels, 'channel'), (connections, 'connection'), (listeners, 'listener'), (queues, 'queue')):
            self.assertEqual({namespace}, {k.split(':')[0] for k in storage.items})

    def test_channel_class(self):
        sut = ChannelRepositoryBuilder(FakeChannel).build()
        channel = sut.create({})
        self.assertIsInstance(channel, FakeChannel)
        channel.add_connection()
        sut.persist(channel)
        self.assertEqual(1, len(list(sut.load_one(channel.id).get_connections())))

    def test_last_call_wins(self):
        custom = KvListenerRepository(InMemoryStorage(), listener_factory=MyListener)
        sut = ChannelRepositoryBuilder(SSEChannel).listeners_repository(custom).listeners().build()
        self.assertIs(MessageQueueListener, type(sut.create({}).add_connection().listener))

        sut = ChannelRepositoryBuilder(SSEChannel).listeners().listeners_repository(custom).build()
        self.assertIsInstance(sut.create({}).add_connection().listener, MyListener)

    def test_repositories_sharing_a_storage(self):
        """Two builds over the same storage simulate producer and consumer sides of an application."""
        storage = InMemoryStorage()
        builder = ChannelRepositoryBuilder(SSEChannel, storage)
        producer, consumer = builder.build(), builder.build()
        self.assertIsNot(producer, consumer)

        channel = producer.create({})
        connection = channel.add_connection()
        producer.persist(channel)

        # No persist after dispatch: queues hold their messages (InMemoryStorage shares queue references)
        producer.load_one(channel.id).dispatch(connection.id, Message(msg_type='test', msg_payload='hi'))

        loaded = consumer.load_one(channel.id)
        loaded.get_connection(connection.id).listener.start()
        self.assertEqual('hi', loaded.deliver_next(connection.id).payload)

        consumer.delete(channel.id)
        with self.assertRaises(ItemNotFound):
            producer.load_one(channel.id)
