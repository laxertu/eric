import pickle
from typing import Iterable
from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.prefabs import DataProcessingChannel, SSEChannel
from eric_sse.contracts.error_handling import ChannelErrorHandlingContract
from eric_sse.exception import NoMessagesException
from eric_sse.message import MessageContract
from eric_sse.queues import Queue
from eric_sse.repository import InMemoryStorage


class SSEChannelErrorHandlingTestCase(ChannelErrorHandlingContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel)

    def channel_data(self) -> dict:
        return {'retry_timeout_milliseconds': 10}


class DataProcessingChannelErrorHandlingTestCase(ChannelErrorHandlingContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(DataProcessingChannel)

    def channel_data(self) -> dict:
        return {'max_workers': 2}


class PicklingStorage(InMemoryStorage):
    """Stores values pickled, as serialising storages (Redis, SQLite, ...) do."""

    def fetch_by_prefix(self, prefix: str) -> Iterable:
        return [pickle.loads(value) for value in super().fetch_by_prefix(prefix)]

    def upsert(self, key: str, value):
        super().upsert(key, pickle.dumps(value))

    def fetch_one(self, key: str):
        return pickle.loads(super().fetch_one(key))


class ListQueue(Queue):
    """Picklable queue, as queues persisted by serialising storages must be."""

    def __init__(self):
        self.messages = []

    def push(self, message: MessageContract) -> None:
        self.messages.append(message)

    def pop(self, timeout: float = 0) -> MessageContract:
        if not self.messages:
            raise NoMessagesException
        return self.messages.pop(0)


class SerialisingStorageErrorHandlingTestCase(ChannelErrorHandlingContract, IsolatedAsyncioTestCase):
    def create_builder(self) -> ChannelRepositoryBuilder:
        return ChannelRepositoryBuilder(SSEChannel, PicklingStorage()).queues(ListQueue)

    def channel_data(self) -> dict:
        return {'retry_timeout_milliseconds': 10}
