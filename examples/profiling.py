from docs.generate_class_diagrams import MessageQueueListener
from eric_sse.connection import Connection
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.profiling import ProfiledListener, ProfiledQueue
from eric_sse.queue_patterns import ReliableQueue
from eric_sse.queues import InMemoryQueue

channel = SSEChannel()
queue = ProfiledQueue(ReliableQueue())
listener = ProfiledListener(MessageQueueListener())
channel.register_connection(Connection(listener=listener, queue=queue))

for _ in range(100):
    channel.dispatch(listener.id, Message(msg_type="test", msg_payload="test"))

# ... dispatch and stream messages

print(queue.push_stats.calls, queue.push_stats.mean_time)
print(listener.on_message_stats.total_time)
