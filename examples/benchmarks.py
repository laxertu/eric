import sys, asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from random import uniform
from time import sleep

from eric_sse.entities import Message
from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import DataProcessingChannel
from eric_sse.benchmark import DataProcessingChannelBenchMark

from eric_sse import get_logger
logger = get_logger()

class IOBoundProcessListener(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        sleep(0.2)
        logger.debug(f"Received {msg.type}: {msg.payload}")

class CPUBoundProcessListener(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        for i in range(0, 1000):
            x = uniform(0, 1)

            for j in range(0, 100):
                y = uniform(0, 1)
                _ = x * y

try:
    max_workers = int(sys.argv[1])
except (IndexError, ValueError):
    max_workers = 6

try:
    num_messages = int(sys.argv[2])
except (IndexError, ValueError):
    num_messages = 50


async def do_benchmark(channel: DataProcessingChannel, listener: MessageQueueListener):


    benchmark = DataProcessingChannelBenchMark(channel)
    wrapped_listener = benchmark.add_listener(listener=listener)

    for _ in range(num_messages):
        channel.dispatch(wrapped_listener.id, Message(msg_type='test'))

    await benchmark.run(wrapped_listener)

async def main():


    threaded_channel = DataProcessingChannel(executor_class=ThreadPoolExecutor, max_workers=max_workers)
    process_channel = DataProcessingChannel(executor_class=ProcessPoolExecutor, max_workers=max_workers)

    io_bound_listener = IOBoundProcessListener()
    cpu_bound_listener = CPUBoundProcessListener()

    for listener in [io_bound_listener, cpu_bound_listener]:
        for channel in [threaded_channel, process_channel]:
            print(f'Launching benchmark of {num_messages} messages and max_workers: {max_workers} {channel.executor_class} {type(listener)}')
            await do_benchmark(channel=channel, listener=listener)

asyncio.run(main())
