import time

from eric_sse.entities import MessageQueueListener
from eric_sse.prefabs import DataProcessingChannel
from eric_sse import get_logger

logger = get_logger()

class DataProcessingChannelBenchMark:

    def __init__(self, channel: DataProcessingChannel):
        self.channel = channel

    async def run(self, listener: MessageQueueListener):
        start = time.time()
        async for _ in self.channel.process_queue(listener):
            pass
        logger.info(f"[BENCHMARK] Message processing time: {time.time() - start}")

