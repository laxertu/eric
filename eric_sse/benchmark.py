import time

from eric_sse.entities import MessageQueueListener
from eric_sse.message import MessageContract
from eric_sse.prefabs import DataProcessingChannel
from eric_sse import get_logger

logger = get_logger()

class ListenerWrapper(MessageQueueListener):
    """Wraps a listener to benchmark its on_message method."""

    def __init__(self, listener: MessageQueueListener):
        super().__init__()
        self.listener = listener

    def on_message(self, msg: MessageContract) -> None:
        """Performs on_message benchmarking"""
        start = time.time()
        self.listener.on_message(msg)
        logger.info(f"[BENCHMARK][MESSAGE] processing time: {time.time() - start}")


class DataProcessingChannelBenchMark:

    def __init__(self, channel: DataProcessingChannel):
        """Wraps a channel to benchmark its process_queue method."""
        self.channel = channel

    def add_listener(self, listener: MessageQueueListener) -> ListenerWrapper:
        """Adds a listener to the channel after having wrapped it"""
        wrapper = ListenerWrapper(listener)
        self.channel.register_listener(wrapper)
        return wrapper

    async def run(self, listener: ListenerWrapper):
        """Runs benchmark"""
        start = time.time()
        async for _ in self.channel.process_queue(listener):
            pass
        logger.info(f"[BENCHMARK][QUEUE] processing time: {time.time() - start}")

