import sys
from eric_sse.entities import Message
from eric_sse.prefabs import DataProcessingChannel
from eric_sse.benchmark import DataProcessingChannelBenchMark

try:
    max_workers = sys.argv[1]
except IndexError:
    max_workers = 6

print(f'Launching benchmark with max_workers: {max_workers}')

in_memory_threading_channel = DataProcessingChannel(max_workers=max_workers)
listener = in_memory_threading_channel.add_listener()

for _ in range(50000):
    in_memory_threading_channel.dispatch(listener.id, Message(msg_type='test'))

benchmark = DataProcessingChannelBenchMark(in_memory_threading_channel)
benchmark.run(listener)
