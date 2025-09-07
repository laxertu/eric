from unittest import TestCase

from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannel, SSEChannelRepository
from eric_sse.queues import InMemoryQueue
from eric_sse.repository import ConnectionRepository, InMemoryStorage
from eric_sse.interfaces import ListenerRepositoryInterface, QueueRepositoryInterface
from eric_sse.connection import InMemoryConnectionsFactory

class FakeListenerRepository(ListenerRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def load(self, connection_id: str) -> MessageQueueListener:
        return self.storage.fetch_one(connection_id)

    def persist(self, connection_id: str, listener: MessageQueueListener):
        self.storage.upsert(connection_id, listener)

    def delete(self, connection_id: str):
        self.storage.delete(connection_id)

class FakeQueueRepository(QueueRepositoryInterface):
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

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

        sut = SSEChannelRepository(
            storage=channels_storage,
            connections_repository=FakeConnectionRepository(
                storage=connections_storage,
                listeners_repository=FakeListenerRepository(listeners_storage),
                queues_repository=FakeQueueRepository(queues_storage)
            ),
            connections_factory=InMemoryConnectionsFactory()
        )
        return sut

    def test_load_ome_on_a_persisted_channel(self):
        sut = self._create_sut()
        self.assertIsInstance(sut, SSEChannelRepository)

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
        listener = channel.add_listener()
        sut.persist(channel)

        sut_2 = self._create_sut()
        channel_2 = sut_2.load_one(channel_id=channel.id)
        self.assertIsInstance(channel_2.get_listener(listener_id=listener.id), MessageQueueListener)

    def test_deletions(self):
        sut = self._create_sut()

        channel = SSEChannel()
        sut.persist(channel)
        self.assertEqual(1, len([c for c in sut.load_all()]))

        sut.delete(channel_id=channel.id)
        self.assertEqual(0, len([c for c in sut.load_all()]))

