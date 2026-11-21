<a id="queue-patterns"></a>

# Queue patterns

Common messaging patterns, in the `eric_sse.queue_patterns` module.

<a id="dead-letter"></a>

# Dead Letter

Built on [error handlers](error_handling.md).

A message is *dead-lettered* when it can’t be delivered or processed: instead of being lost, it goes to a separate
queue, the dead letter queue, where it can be inspected, redelivered or discarded later.

[`DeadLetterHandler`](reference/queue_patterns.md#eric_sse.queue_patterns.DeadLetterHandler) dead-letters a message when:

* pushing it to a listener’s queue fails, e.g. the queue backend is down. The channel still re-raises the error (or logs it, in a broadcast);
* the listener’s [`on_message()`](reference/entities.md#eric_sse.listener.MessageQueueListener.on_message) raises. The channel still delivers the message.

Pop errors are not dead-lettered, because no message is available when they occur.

**Setup**

The handler is both a queuing and a listener error handler: register the same instance for both.
On a single channel:

```python
from eric_sse.prefabs import SSEChannel
from eric_sse.queue_patterns import DeadLetterHandler

dead_letters = DeadLetterHandler()
channel = SSEChannel()
channel.add_queuing_error_handler(dead_letters)
channel.add_listener_error_handler(dead_letters)
```

or on every channel created or loaded by a repository:

```python
from eric_sse.builder import ChannelRepositoryBuilder

channels = (
    ChannelRepositoryBuilder(SSEChannel)
    .queuing_error_handler(dead_letters)
    .listener_error_handler(dead_letters)
    .build()
)
```

**What is stored**

Each failed message is pushed as a [`DeadLetter`](reference/queue_patterns.md#eric_sse.queue_patterns.DeadLetter), that wraps it and adds:

* `connection_id`: the connection the message was meant for;
* `error`: the `repr()` of the exception;
* `message`: the original message, of its original class (e.g. a [`SignedMessage`](reference/entities.md#eric_sse.message.SignedMessage) keeps its sender).

A `DeadLetter` is a message itself, with the original `id`, `type` and `payload`.

**Inspecting and redelivering**

```python
from eric_sse.exception import NoMessagesException

while True:
    try:
        dead_letter = dead_letters.queue.pop()
    except NoMessagesException:
        break
    print(dead_letter.connection_id, dead_letter.type, dead_letter.error)
    channel.dispatch(dead_letter.connection_id, dead_letter.message)
```

If the connection no longer exists, `dispatch` raises an [`InvalidConnectionException`](reference/exceptions.md#eric_sse.exception.InvalidConnectionException).

**Choosing the dead letter queue**

By default it’s an [`InMemoryQueue`](reference/entities.md#eric_sse.queues.InMemoryQueue): dead letters are lost when the process ends.
To keep them, pass a durable queue: `DeadLetterHandler(queue)`. `DeadLetter` can be pickled, provided the original message can.

One dead letter queue can serve many channels, but it doesn’t record the channel: use one handler per channel if you
need to know where a message came from.

**When the dead letter queue fails**

The handler never raises: if pushing to the dead letter queue fails too, the error is logged and the message is lost.
This way, the channel goes on with the original error as if no handler was registered.

**Customising**

Override [`_dead_letter()`](reference/queue_patterns.md#eric_sse.queue_patterns.DeadLetterHandler._dead_letter) to change what is stored, e.g. to add a timestamp
or to skip some message types:

```python
class SelectiveDeadLetterHandler(DeadLetterHandler):
    def _dead_letter(self, connection_id, msg, exception):
        if msg.type != 'heartbeat':
            super()._dead_letter(connection_id, msg, exception)
```

<a id="reliable-queue"></a>

# Reliable Queue

With a plain queue, a message is gone once popped: if the consumer fails before handling it, e.g. the SSE client
disconnects, it’s lost. [`ReliableQueue`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue) keeps popped messages *in flight* until they
are acknowledged, so they can be delivered again. Delivery is *at least once*.

* [`pop()`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue.pop) and [`wait_pop()`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue.wait_pop)
  return a [`ReliableMessage`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableMessage) and keep it in flight;
* [`ack()`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue.ack) removes it for good, once it’s been handled;
* [`nack()`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue.nack) puts it back in the queue at once;
* a message not acknowledged within `visibility_timeout` seconds is put back in the queue by
  [`requeue_expired()`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue.requeue_expired), that `pop` and `wait_pop` call before popping.
  With `visibility_timeout=None` it stays in flight until `nack`.

Requeued messages go to the end of the queue.

**Usage**

```python
from eric_sse.queue_patterns import ReliableQueue

queue = ReliableQueue(visibility_timeout=30)
queue.push(Message(msg_type='order', msg_payload={'id': 1}))

msg = queue.pop()
try:
    handle(msg.message)
    queue.ack(msg.id)
except Exception:
    queue.nack(msg.id)
```

`ack` and `nack` return `False` if the message isn’t in flight: unknown id, already acknowledged, or already put
back in the queue because its visibility timeout expired. In the last case it will be delivered again.

**What is returned**

A [`ReliableMessage`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableMessage) wraps the pushed message and adds:

* `id`: a new id to acknowledge it with, kept across redeliveries. It replaces the original message’s id;
* `deliveries`: how many times it has been popped. More than 1 means it is a redelivery;
* `message`: the original message.

It is a message itself, with the original `type` and `payload`.

**With channels**

A `ReliableQueue` is a [`Queue`](reference/entities.md#eric_sse.queues.Queue), so a channel can use it for its connections, e.g. through a
custom [`ConnectionsFactory`](reference/entities.md#eric_sse.connection.ConnectionsFactory) or [`queues()`](reference/persistence.md#eric_sse.builder.ChannelRepositoryBuilder.queues).
[`SSEChannel`](reference/prefabs.md#eric_sse.prefabs.SSEChannel) sends the message id as the SSE `id` field, so a client can acknowledge what it
received, e.g. calling an endpoint of your application that calls `ack`.

**Durability**

`ReliableQueue` wraps a queue for messages waiting to be popped, and a [`KvStorage`](reference/persistence.md#eric_sse.repository.KvStorage) for
in-flight ones. Both default to in-memory implementations. With durable ones, unacknowledged messages survive a restart:

```python
queue = ReliableQueue(queue=my_durable_queue, visibility_timeout=30, in_flight=my_durable_storage)
```

It can be pickled if both can, so it can be persisted by a queue repository.

See [Queue patterns](reference/queue_patterns.md) for the classes.
