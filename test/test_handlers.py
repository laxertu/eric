from unittest import IsolatedAsyncioTestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.prefabs import DataProcessingChannel, SSEChannel
from eric_sse.contracts.error_handling import ChannelErrorHandlingContract


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
