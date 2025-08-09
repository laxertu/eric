from unittest import TestCase
from eric_sse.inmemory import InMemoryStorage, ChannelRepository, ConnectionRepository, QueueRepository


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

    def test_entities(self):
        sut = InMemoryStorage()
        sut.upsert('abc', 1)