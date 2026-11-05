from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.profiling import ProfiledListener, ProfiledQueue
from eric_sse.queue_patterns import ReliableQueue

# Every connection created by the repository gets a profiled listener and a profiled queue
channels = (
    ChannelRepositoryBuilder(SSEChannel)
    .listeners(lambda: ProfiledListener(MessageQueueListener()))
    .queues(lambda: ProfiledQueue(ReliableQueue()))
    .build()
)

channel = channels.create({})
listener = channel.add_listener()
listener.start()

for _ in range(100):
    channel.dispatch(listener.id, Message(msg_type="test", msg_payload="test"))
for _ in range(100):
    channel.deliver_next(listener.id)

for connection in channel.get_connections():
    print(f'listener {connection.listener.id}')
    print(f'  on_message: {connection.listener.on_message_stats.calls} calls, {connection.listener.on_message_stats.total_time:.6f} s')
    print(f'  push: {connection.queue.push_stats.calls} calls, mean {connection.queue.push_stats.mean_time:.6f} s')
    print(f'  pop: {connection.queue.pop_stats.calls} calls, mean {connection.queue.pop_stats.mean_time:.6f} s')
