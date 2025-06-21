import time

from eric_sse.entities import MessageQueueListener
from eric_sse.prefabs import DataProcessingChannel
from eric_sse import get_logger

logger = get_logger()

class DataProcessingChannelBenchMark:

    def __init__(self, channel: DataProcessingChannel):
        self.channel = channel

    def run(self, listener: MessageQueueListener):
        start = time.time()
        self.channel.process_queue(listener)
        logger.info(f"Message processing time: {time.time() - start}")

