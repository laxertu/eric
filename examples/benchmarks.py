import sys, asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from random import uniform, random
from time import sleep

from eric_sse.entities import Message, MessageQueueListener
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


async def do_benchmark(channel: DataProcessingChannel, listener: MessageQueueListener, num_messages: int):

    channel.register_listener(listener)
    listener.start_sync()

    for _ in range(num_messages):
        channel.dispatch(listener.id, Message(msg_type='test'))

    benchmark = DataProcessingChannelBenchMark(channel)
    await benchmark.run(listener)

async def main():

    mum_messages = 50

    threaded_channel = DataProcessingChannel(executor_class=ThreadPoolExecutor, max_workers=max_workers)
    process_channel = DataProcessingChannel(executor_class=ProcessPoolExecutor, max_workers=max_workers)

    io_bound_listener = IOBoundProcessListener()
    cpu_bound_listener = CPUBoundProcessListener()

    for channel in [threaded_channel, process_channel]:
        for listener in [io_bound_listener, cpu_bound_listener]:
            print(f'Launching benchmark with max_workers: {max_workers} {channel.executor_class} {type(listener)}')
            await do_benchmark(channel=channel, listener=listener, num_messages=mum_messages)



asyncio.run(main())
