from unittest import TestCase

import pytest

from eric_sse.exception import RepositoryError
from eric_sse.inmemory import InMemoryStorage, InMemoryChannelRepository, InMemoryConnectionRepository
from eric_sse.prefabs import SSEChannel


class TestInMemory(TestCase):

    def test_storage(self):
        sut = InMemoryStorage()

        sut.upsert('abc', 1)
        sut.upsert('abcde', 2)
        self.assertEqual(sut.fetch_one('abc'), 1)

        self.assertEqual([x for x in sut.fetch_all()], [1, 2])
        self.assertEqual([x for x in sut.fetch_by_prefix('ab')], [1, 2])
        self.assertEqual([x for x in sut.fetch_by_prefix('abcd')], [2])
        self.assertEqual([x for x in sut.fetch_by_prefix('abcde')], [2])
        self.assertEqual([x for x in sut.fetch_by_prefix('zzz')], [])

    def test_channel_repository(self):
        sut = InMemoryChannelRepository()
        channel = SSEChannel()
        listener = channel.add_listener()

        sut.persist(channel)
        channel_clone = sut.load_one(channel_id=channel.id)
        self.assertIs(
            channel_clone.get_listener(listener_id=listener.id),
            channel.get_listener(listener_id=listener.id)
        )

        self.assertIs(
            channel_clone,
            channel,
        )

        sut.delete(channel_id=channel.id)
        with pytest.raises(RepositoryError):
            _ = sut.load_one(channel_id=channel.id)


