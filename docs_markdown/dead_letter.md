<a id="dead-letter"></a>

# Dead Letter

In the `eric_sse.queue_patterns` module. Built on [error handlers](error_handling.md).

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

See [Queue patterns](reference/queue_patterns.md) for the classes.
