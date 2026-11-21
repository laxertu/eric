from unittest import TestCase

from eric_sse.builder import ChannelRepositoryBuilder

from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannel, SimpleDistributedApplicationChannel, DataProcessingChannel
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ChannelRepository, ConnectionRepository, InMemoryStorage, KvListenerRepository, KvQueueRepository
from eric_sse.message import Message
from eric_sse.exception import ItemNotFound
from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface

class MyListener(MessageQueueListener):
    pass


class MyQueue(InMemoryQueue):
    pass


class FakeListenerRepository(ListenerRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def create(self) -> MessageQueueListener:
        return MessageQueueListener()

    def load(self, connection_id: str) -> MessageQueueListener:
        return self.storage.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: MessageQueueListener):
        self.storage.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.storage.delete(connection_id)

class FakeQueueRepository(QueueRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def create(self) -> InMemoryQueue:
        return InMemoryQueue()

    def load(self, connection_id: str) -> InMemoryQueue:
        return self.storage.fetch_one(connection_id)

    def persist(self, connection_id: str, queue: InMemoryQueue):
        return self.storage.upsert(connection_id, queue)

    def delete(self, connection_id: str):
        self.storage.delete(connection_id)


class FakeConnectionRepository(ConnectionRepository):
    pass


class TestSSEChannelRepository(TestCase):

    def setUp(self) -> None:
        self.channels_storage = InMemoryStorage()
        self.connections_storage = InMemoryStorage()
        self.listeners_storage = InMemoryStorage()
        self.queues_storage = InMemoryStorage()


    def _create_sut(self):
        channels_storage = self.channels_storage
        connections_storage = self.connections_storage
        listeners_storage = self.listeners_storage
        queues_storage = self.queues_storage

        sut = ChannelRepository(
            storage=channels_storage,
            connections_repository=FakeConnectionRepository(
                storage=connections_storage,
                listeners_repository=FakeListenerRepository(listeners_storage),
                queues_repository=FakeQueueRepository(queues_storage)
            ),
            channel_class=SSEChannel
        )
        return sut

    def test_load_ome_on_a_persisted_channel(self):
        sut = self._create_sut()

        channel = SSEChannel()
        sut.persist(channel)

        sut_2 = self._create_sut()
        channel_2 = sut_2.load_one(channel_id=channel.id)
        self.assertIsInstance(channel_2, SSEChannel)

        self.assertEqual(channel.id, channel_2.id)
        self.assertNotEqual(id(channel), id(channel_2))

    def test_load_a_persisted_listener(self):
        sut = self._create_sut()

        channel = SSEChannel()
        connection = channel.add_connection()
        sut.persist(channel)

        sut_2 = self._create_sut()
        channel_2 = sut_2.load_one(channel_id=channel.id)
        self.assertIsInstance(channel_2.get_connection(connection_id=connection.id).listener, MessageQueueListener)

    def test_deletions(self):
        sut = self._create_sut()

        channel = SSEChannel()
        sut.persist(channel)
        self.assertEqual(1, len([c for c in sut.load_all()]))

        sut.delete(channel_id=channel.id)
        self.assertEqual(0, len([c for c in sut.load_all()]))

    def test_delete_removes_connections_listeners_and_queues(self):
        sut = self._create_sut()
        channel = SSEChannel()
        channel.add_connection()
        channel.add_connection()
        sut.persist(channel)

        sut.delete(channel_id=channel.id)
        for storage in (self.channels_storage, self.connections_storage, self.listeners_storage, self.queues_storage):
            self.assertEqual({}, storage.items)

        sut.delete(channel_id=channel.id)  # Idempotent
        sut.delete(channel_id='never-persisted')

    def test_persist_and_delete_do_not_load_listeners_and_queues(self):
        sut = self._create_sut()
        channel = SSEChannel()
        channel.add_connection()
        removed = channel.add_connection()
        sut.persist(channel)

        loads = []
        listeners_repository = sut.connections_repository.listeners_repository
        queues_repository = sut.connections_repository.queues_repository
        listeners_repository.load = lambda connection_id: loads.append(connection_id)
        queues_repository.load = lambda connection_id: loads.append(connection_id)

        channel.remove_connection(removed.id)
        sut.persist(channel)
        self.assertEqual([c.id for c in channel.get_connections()], list(sut.connections_repository.load_ids(channel.id)))

        sut.delete(channel_id=channel.id)
        self.assertEqual([], loads)



class TestSSEChannelRepositoryBuiltByBuilder(TestCase):

    def test_channel_created_outside_repository_survives_reload(self):
        sut = ChannelRepositoryBuilder(SSEChannel).build()

        channel = SSEChannel(retry_timeout_milliseconds=42)
        connection = channel.add_connection()
        channel.dispatch(connection.id, Message(msg_type='test', msg_payload='hi'))
        sut.persist(channel)

        loaded = sut.load_one(channel.id)
        self.assertEqual(42, loaded.retry_timeout_milliseconds)
        loaded.get_connection(connection.id).listener.start()
        self.assertEqual('hi', loaded.deliver_next(connection.id).payload)


class TestKvRepositories(TestCase):

    def test_listener_repository(self):
        sut = KvListenerRepository(InMemoryStorage())
        listener = MessageQueueListener()
        sut.persist('c1', listener)
        self.assertIs(listener, sut.load('c1'))
        sut.delete('c1')
        with self.assertRaises(ItemNotFound):
            sut.load('c1')

    def test_create(self):
        self.assertIsInstance(KvListenerRepository(InMemoryStorage()).create(), MessageQueueListener)
        self.assertIsInstance(KvListenerRepository(InMemoryStorage(), listener_factory=MyListener).create(), MyListener)
        self.assertIsInstance(KvQueueRepository(InMemoryStorage()).create(), InMemoryQueue)
        self.assertIsInstance(KvQueueRepository(InMemoryStorage(), queue_factory=MyQueue).create(), MyQueue)

        sut = KvQueueRepository(InMemoryStorage())
        self.assertIsNot(sut.create(), sut.create())

    def test_in_memory_queue_is_not_serialisable(self):
        # Its messages must never be saved by accident through a serialising storage
        import pickle
        with self.assertRaises(TypeError):
            pickle.dumps(InMemoryQueue())

    def test_queue_repository(self):
        sut = KvQueueRepository(InMemoryStorage())
        queue = InMemoryQueue()
        sut.persist('c1', queue)
        self.assertIs(queue, sut.load('c1'))
        sut.delete('c1')
        with self.assertRaises(ItemNotFound):
            sut.load('c1')


class TestChannelSerialisation(TestCase):

    def _round_trip(self, channel):
        sut = ChannelRepositoryBuilder(type(channel)).build()
        sut.persist(channel)
        return sut.load_one(channel.id)

    def test_sse_channel(self):
        loaded = self._round_trip(SSEChannel(stream_delay_seconds=3, retry_timeout_milliseconds=42))
        self.assertIsInstance(loaded, SSEChannel)
        self.assertEqual(3, loaded.stream_delay_seconds)
        self.assertEqual(42, loaded.retry_timeout_milliseconds)

    def test_simple_distributed_application_channel(self):
        loaded = self._round_trip(SimpleDistributedApplicationChannel(retry_timeout_milliseconds=42))
        self.assertIs(SimpleDistributedApplicationChannel, type(loaded))
        self.assertEqual(42, loaded.retry_timeout_milliseconds)

    def test_data_processing_channel(self):
        from concurrent.futures import ProcessPoolExecutor
        loaded = self._round_trip(DataProcessingChannel(max_workers=4, executor_class=ProcessPoolExecutor, channel_id='dp'))
        self.assertIsInstance(loaded, DataProcessingChannel)
        self.assertEqual('dp', loaded.id)
        self.assertEqual(4, loaded.max_workers)
        self.assertIs(ProcessPoolExecutor, loaded.executor_class)

    def test_from_dict_injects_connections_factory(self):
        sut = ChannelRepositoryBuilder(SSEChannel).listeners(MyListener).build()
        channel = SSEChannel.from_dict(SSEChannel().to_dict(), connections_factory=sut.connections_repository)
        self.assertIsInstance(channel.add_connection().listener, MyListener)

    def test_persist_rejects_other_channel_classes(self):
        sut = ChannelRepositoryBuilder(SSEChannel).build()
        with self.assertRaises(TypeError):
            sut.persist(SimpleDistributedApplicationChannel())
        self.assertEqual([], list(sut.load_all()))
