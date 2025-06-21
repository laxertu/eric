import time

from eric_sse.entities import MessageQueueListener
from eric_sse.message import MessageContract
from eric_sse.prefabs import DataProcessingChannel
from eric_sse import get_logger

logger = get_logger()

class ListenerWrapper(MessageQueueListener):

    def __init__(self, listener: MessageQueueListener):
        super().__init__()
        self.listener = listener

    def on_message(self, msg: MessageContract) -> None:
        start = time.time()
        self.listener.on_message(msg)
        logger.info(f"[BENCHMARK][MESSAGE] processing time: {time.time() - start}")


class DataProcessingChannelBenchMark:

    def __init__(self, channel: DataProcessingChannel):
        self.channel = channel

    def add_listener(self, listener: MessageQueueListener):
        wrapper = ListenerWrapper(listener)
        self.channel.register_listener(wrapper)
        return wrapper

    async def run(self, listener: MessageQueueListener):
        start = time.time()
        async for _ in self.channel.process_queue(listener):
            pass
        logger.info(f"[BENCHMARK][QUEUE] processing time: {time.time() - start}")

