import time

from eric_sse.listener import MessageQueueListener
from eric_sse.message import MessageContract
from eric_sse.prefabs import DataProcessingChannel
from eric_sse import get_logger

logger = get_logger()

class ListenerWrapper(MessageQueueListener):
    """Wraps a listener to profile its on_message method."""

    def __init__(self, listener: MessageQueueListener, profile_messages: bool = False):
        super().__init__()
        self.listener = listener
        self.profile_messages = profile_messages

    async def on_message(self, msg: MessageContract) -> None:
        """Performs on_message profiling"""
        start = time.time()
        await self.listener.on_message(msg)

        if self.profile_messages:
            logger.info(f"[PROFILER][MESSAGE] processing time: {time.time() - start}")


class DataProcessingChannelProfiler:

    def __init__(self, channel: DataProcessingChannel):
        """Wraps a channel to profile its process_queue method."""
        self.channel = channel

    async def add_listener(self, listener: MessageQueueListener) -> ListenerWrapper:
        """Adds a listener to the channel after having wrapped it"""
        wrapper = ListenerWrapper(listener)
        await self.channel.register_listener(wrapper)
        return wrapper

    async def run(self, listener: ListenerWrapper):
        """Runs profile"""
        start = time.time()
        async for _ in self.channel.process_queue(listener):
            pass
        logger.info(f"[PROFILER][QUEUE] processing time: {time.time() - start}")

