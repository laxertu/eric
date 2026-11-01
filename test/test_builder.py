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
        sut = ChannelRepositoryBuilder().build()
        self.assertIsInstance(sut, ChannelRepository)
        self.assertIs(SSEChannel, sut.channel_class)

        channel = sut.create({'retry_timeout_milliseconds': 42})
        self.assertIsInstance(channel, SSEChannel)
        listener = channel.add_listener()
        sut.persist(channel)

        loaded = sut.load_one(channel.id)
        self.assertEqual(42, loaded.retry_timeout_milliseconds)
        self.assertIsInstance(loaded.get_listener(listener.id), MessageQueueListener)
        self.assertIsInstance(next(iter(loaded.get_connections())).queue, InMemoryQueue)

    def test_storage_layout(self):
        storage = InMemoryStorage()
        sut = ChannelRepositoryBuilder(storage).build()
        channel = sut.create({})
        channel.add_listener()
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
        sut = ChannelRepositoryBuilder(storage).build()
        sut.create({}).add_listener()
        self.assertEqual({}, storage.items)

    def test_listener_and_queue_classes(self):
        sut = ChannelRepositoryBuilder().listeners(MyListener).queues(MyQueue).build()

        channel = sut.create({})
        self.assertIsInstance(channel.add_listener(), MyListener)
        sut.persist(channel)

        loaded = sut.load_one(channel.id)
        self.assertIsInstance(loaded.add_listener(), MyListener)
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
            ChannelRepositoryBuilder()
            .listeners_repository(KvListenerRepository(InMemoryStorage(), listener_class=MyListener))
            .queues_repository(MyQueueRepository(InMemoryStorage(), queue_factory=MyQueue))
            .build()
        )
        channel = sut.create({})
        self.assertIsInstance(channel.add_listener(), MyListener)
        connection = next(iter(channel.get_connections()))
        self.assertIsInstance(connection.queue, MyQueue)
        sut.persist(channel)

        sut.delete(channel.id)
        self.assertEqual([connection.id], deleted)

    def test_dedicated_storages(self):
        default, channels, connections, listeners, queues = (InMemoryStorage() for _ in range(5))
        sut = (
            ChannelRepositoryBuilder(default)
            .channels(storage=channels)
            .connections(connections)
            .listeners(storage=listeners)
            .queues(storage=queues)
            .build()
        )
        channel = sut.create({})
        channel.add_listener()
        sut.persist(channel)

        self.assertEqual({}, default.items)
        for storage, namespace in ((channels, 'channel'), (connections, 'connection'), (listeners, 'listener'), (queues, 'queue')):
            self.assertEqual({namespace}, {k.split(':')[0] for k in storage.items})

    def test_channel_class(self):
        sut = ChannelRepositoryBuilder().channels(FakeChannel).build()
        channel = sut.create({})
        self.assertIsInstance(channel, FakeChannel)
        channel.add_listener()
        sut.persist(channel)
        self.assertEqual(1, len(list(sut.load_one(channel.id).get_connections())))

    def test_last_call_wins(self):
        custom = KvListenerRepository(InMemoryStorage(), listener_class=MyListener)
        sut = ChannelRepositoryBuilder().listeners_repository(custom).listeners().build()
        self.assertIs(MessageQueueListener, type(sut.create({}).add_listener()))

        sut = ChannelRepositoryBuilder().listeners().listeners_repository(custom).build()
        self.assertIsInstance(sut.create({}).add_listener(), MyListener)

    def test_repositories_sharing_a_storage(self):
        """Two builds over the same storage simulate producer and consumer sides of an application."""
        storage = InMemoryStorage()
        builder = ChannelRepositoryBuilder(storage)
        producer, consumer = builder.build(), builder.build()
        self.assertIsNot(producer, consumer)

        channel = producer.create({})
        listener = channel.add_listener()
        producer.persist(channel)

        # No persist after dispatch: queues hold their messages (InMemoryStorage shares queue references)
        producer.load_one(channel.id).dispatch(listener.id, Message(msg_type='test', msg_payload='hi'))

        loaded = consumer.load_one(channel.id)
        loaded.get_listener(listener.id).start()
        self.assertEqual('hi', loaded.deliver_next(listener.id).payload)

        consumer.delete(channel.id)
        with self.assertRaises(ItemNotFound):
            producer.load_one(channel.id)
