from unittest import TestCase

from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannel, SSEChannelRepository
from eric_sse.repository import ConnectionRepository
from eric_sse.inmemory import InMemoryStorage, InMemoryQueueRepository, InMemoryListenerRepository
from eric_sse.connection import InMemoryConnectionsFactory


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
                listeners_repository=InMemoryListenerRepository(listeners_storage),
                queues_repository=InMemoryQueueRepository(queues_storage),
                connections_factory=InMemoryConnectionsFactory()
            )
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

