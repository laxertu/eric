<a id="module-eric_sse.queue_patterns"></a>

<a id="queue-patterns"></a>

# Queue patterns

Messaging patterns built on queues and [`handlers`](handlers.md#module-eric_sse.handlers).

<a id="eric_sse.queue_patterns.DeadLetter"></a>

### *class* DeadLetter

Bases: [`MessageContract`](entities.md#eric_sse.message.MessageContract)

A message that could not be delivered or processed, plus where it was going and why it failed.

It wraps the original message: [`id`](#eric_sse.queue_patterns.DeadLetter.id), [`type`](#eric_sse.queue_patterns.DeadLetter.type) and [`payload`](#eric_sse.queue_patterns.DeadLetter.payload) are the original ones,
and [`message`](#eric_sse.queue_patterns.DeadLetter.message) keeps its class, e.g. a [`SignedMessage`](entities.md#eric_sse.message.SignedMessage) with its sender.

To redeliver it: `channel.dispatch(dead_letter.connection_id, dead_letter.message)`.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Id of the connection the message was meant for.
  * **message** ([*MessageContract*](entities.md#eric_sse.message.MessageContract)) – The original message.
  * **error** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Description of the error, e.g. `repr()` of the exception.

<a id="eric_sse.queue_patterns.DeadLetter.__init__"></a>

#### \_\_init_\_(connection_id, message, error)

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **message** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **error** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.queue_patterns.DeadLetter.connection_id"></a>

#### *property* connection_id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Id of the connection the message was meant for.

<a id="eric_sse.queue_patterns.DeadLetter.message"></a>

#### *property* message *: [MessageContract](entities.md#eric_sse.message.MessageContract)*

The original message.

<a id="eric_sse.queue_patterns.DeadLetter.error"></a>

#### *property* error *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Description of the error.

<a id="eric_sse.queue_patterns.DeadLetter.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Optional message identifier, e.g. the “id” field of an SSE event. None if the message has none.

<a id="eric_sse.queue_patterns.DeadLetter.type"></a>

#### *property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.queue_patterns.DeadLetter.payload"></a>

#### *property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.queue_patterns.DeadLetterHandler"></a>

### *class* DeadLetterHandler

Bases: [`QueuingErrorHandler`](handlers.md#eric_sse.handlers.QueuingErrorHandler), [`ListenerErrorHandler`](handlers.md#eric_sse.handlers.ListenerErrorHandler)

Dead Letter pattern: messages that could not be delivered or processed are pushed to a dead letter queue,
wrapped in a [`DeadLetter`](#eric_sse.queue_patterns.DeadLetter).

A message is dead-lettered when:

* pushing it to a listener’s queue fails, see [`handle_push_error()`](#eric_sse.queue_patterns.DeadLetterHandler.handle_push_error);
* the listener’s [`on_message()`](entities.md#eric_sse.listener.MessageQueueListener.on_message) fails, see [`handle_on_message_error()`](#eric_sse.queue_patterns.DeadLetterHandler.handle_on_message_error).

Pop errors are not dead-lettered: no message is available when they occur.

Register the same instance for both kinds of errors:

```default
dead_letters = DeadLetterHandler()
channel.add_queuing_error_handler(dead_letters)
channel.add_listener_error_handler(dead_letters)
```

or, for every channel of a repository, with
[`queuing_error_handler()`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder.queuing_error_handler) and
[`listener_error_handler()`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder.listener_error_handler).

If pushing to the dead letter queue fails too, the error is logged and the message is lost:
the handler never raises, so the original error is the one the channel re-raises or logs.

* **Parameters:**
  **queue** ([*Queue*](entities.md#eric_sse.queues.Queue)) – The dead letter queue. Defaults to an [`InMemoryQueue`](entities.md#eric_sse.queues.InMemoryQueue).

<a id="eric_sse.queue_patterns.DeadLetterHandler.__init__"></a>

#### \_\_init_\_(queue=None)

* **Parameters:**
  **queue** ([*Queue*](entities.md#eric_sse.queues.Queue) *[*[*DeadLetter*](#eric_sse.queue_patterns.DeadLetter) *,* [*DeadLetter*](#eric_sse.queue_patterns.DeadLetter) *]*  *|* *None*)

<a id="eric_sse.queue_patterns.DeadLetterHandler.queue"></a>

#### *property* queue *: [Queue](entities.md#eric_sse.queues.Queue)[[DeadLetter](#eric_sse.queue_patterns.DeadLetter), [DeadLetter](#eric_sse.queue_patterns.DeadLetter)]*

The dead letter queue, e.g. to inspect or redeliver its messages.

<a id="eric_sse.queue_patterns.DeadLetterHandler.handle_push_error"></a>

#### handle_push_error(connection_id, msg, exception)

Called when pushing **msg** to the queue of connection **connection_id** fails. The exception is re-raised afterwards.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.queue_patterns.DeadLetterHandler.handle_on_message_error"></a>

#### handle_on_message_error(connection_id, msg, exception)

Called when [`on_message()`](entities.md#eric_sse.listener.MessageQueueListener.on_message) of connection **connection_id** fails.
The exception is not re-raised: **msg** is delivered anyway.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.queue_patterns.DeadLetterHandler._dead_letter"></a>

#### \_dead_letter(connection_id, msg, exception)

Pushes **msg** to the dead letter queue, wrapped in a [`DeadLetter`](#eric_sse.queue_patterns.DeadLetter). Override to change what is stored.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.queue_patterns.ReliableMessage"></a>

### *class* ReliableMessage

Bases: [`MessageContract`](entities.md#eric_sse.message.MessageContract)

A message popped from a [`ReliableQueue`](#eric_sse.queue_patterns.ReliableQueue): the original message plus an id to acknowledge it with.

[`type`](#eric_sse.queue_patterns.ReliableMessage.type) and [`payload`](#eric_sse.queue_patterns.ReliableMessage.payload) are the original ones, and [`message`](#eric_sse.queue_patterns.ReliableMessage.message) keeps its class.

* **Parameters:**
  * **message_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Id to pass to [`ReliableQueue.ack()`](#eric_sse.queue_patterns.ReliableQueue.ack) or [`ReliableQueue.nack()`](#eric_sse.queue_patterns.ReliableQueue.nack).
  * **message** ([*MessageContract*](entities.md#eric_sse.message.MessageContract)) – The original message.
  * **deliveries** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – How many times the message has been popped, this time included.

<a id="eric_sse.queue_patterns.ReliableMessage.__init__"></a>

#### \_\_init_\_(message_id, message, deliveries=0)

* **Parameters:**
  * **message_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **message** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **deliveries** ([*int*](https://docs.python.org/3/builtins/functions.html#int))

<a id="eric_sse.queue_patterns.ReliableMessage.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Id to acknowledge the message with. It replaces the original message’s id, if any.

<a id="eric_sse.queue_patterns.ReliableMessage.message"></a>

#### *property* message *: [MessageContract](entities.md#eric_sse.message.MessageContract)*

The original message.

<a id="eric_sse.queue_patterns.ReliableMessage.deliveries"></a>

#### *property* deliveries *: [int](https://docs.python.org/3/builtins/functions.html#int)*

How many times the message has been popped: more than 1 means it is a redelivery.

<a id="eric_sse.queue_patterns.ReliableMessage.type"></a>

#### *property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.queue_patterns.ReliableMessage.payload"></a>

#### *property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.queue_patterns.ReliableQueue"></a>

### *class* ReliableQueue

Bases: [`Queue`](entities.md#eric_sse.queues.Queue)[[`MessageContract`](entities.md#eric_sse.message.MessageContract), [`ReliableMessage`](#eric_sse.queue_patterns.ReliableMessage)]

Reliable Queue pattern: a popped message isn’t removed, it is moved to an in-flight storage until it is acknowledged.

* [`pop()`](#eric_sse.queue_patterns.ReliableQueue.pop) and [`wait_pop()`](#eric_sse.queue_patterns.ReliableQueue.wait_pop) return a [`ReliableMessage`](#eric_sse.queue_patterns.ReliableMessage);
* [`ack()`](#eric_sse.queue_patterns.ReliableQueue.ack) removes it for good, once it has been handled, e.g. when the client confirms it got it;
* [`nack()`](#eric_sse.queue_patterns.ReliableQueue.nack) puts it back in the queue at once;
* messages not acknowledged within **visibility_timeout** seconds are put back in the queue by [`requeue_expired()`](#eric_sse.queue_patterns.ReliableQueue.requeue_expired),
  that [`pop()`](#eric_sse.queue_patterns.ReliableQueue.pop) and [`wait_pop()`](#eric_sse.queue_patterns.ReliableQueue.wait_pop) call before popping.

Delivery is *at least once*: a message acknowledged after its visibility timeout may already have been put back,
and is delivered again. Re-queued messages go to the end of the queue.

It wraps another queue, that keeps the messages waiting to be popped, and a [`KvStorage`](persistence.md#eric_sse.repository.KvStorage)
for in-flight messages. With durable ones, unacknowledged messages survive a restart.
It can be pickled if both can, so it can be persisted by a queue repository.

* **Parameters:**
  * **queue** ([*Queue*](entities.md#eric_sse.queues.Queue)) – Queue of messages waiting to be popped. Defaults to an [`InMemoryQueue`](entities.md#eric_sse.queues.InMemoryQueue).
  * **visibility_timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*) – Seconds a popped message can stay unacknowledged. None: until [`nack()`](#eric_sse.queue_patterns.ReliableQueue.nack).
  * **in_flight** ([*KvStorage*](persistence.md#eric_sse.repository.KvStorage)) – Storage of popped messages not yet acknowledged. Defaults to an [`InMemoryStorage`](persistence.md#eric_sse.repository.InMemoryStorage).

<a id="eric_sse.queue_patterns.ReliableQueue.__init__"></a>

#### \_\_init_\_(queue=None, visibility_timeout=30.0, in_flight=None)

* **Parameters:**
  * **queue** ([*Queue*](entities.md#eric_sse.queues.Queue) *[*[*ReliableMessage*](#eric_sse.queue_patterns.ReliableMessage) *,* [*ReliableMessage*](#eric_sse.queue_patterns.ReliableMessage) *]*  *|* *None*)
  * **visibility_timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)
  * **in_flight** ([*KvStorage*](persistence.md#eric_sse.repository.KvStorage) *|* *None*)

<a id="eric_sse.queue_patterns.ReliableQueue.push"></a>

#### push(message)

Pushes **message**, wrapped in a [`ReliableMessage`](#eric_sse.queue_patterns.ReliableMessage) with a new id.

* **Parameters:**
  **message** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.queue_patterns.ReliableQueue.pop"></a>

#### pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*ReliableMessage*](#eric_sse.queue_patterns.ReliableMessage)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available, after waiting
**timeout** seconds.

<a id="eric_sse.queue_patterns.ReliableQueue.wait_pop"></a>

#### *async* wait_pop(timeout)

Waits for the next message without blocking the event loop.

The default implementation runs [`pop()`](#eric_sse.queue_patterns.ReliableQueue.pop) with **timeout** in a worker thread, so it takes one thread
per waiting call. Override it with a native async wait when possible.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message.
* **Return type:**
  [*ReliableMessage*](#eric_sse.queue_patterns.ReliableMessage)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="eric_sse.queue_patterns.ReliableQueue.ack"></a>

#### ack(message_id)

Acknowledges a popped message, that is removed for good.

Returns False if it isn’t in flight: unknown, already acknowledged, or put back in the queue.

* **Parameters:**
  **message_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [bool](https://docs.python.org/3/builtins/functions.html#bool)

<a id="eric_sse.queue_patterns.ReliableQueue.nack"></a>

#### nack(message_id)

Puts a popped message back in the queue at once.

Returns False if it isn’t in flight: unknown, already acknowledged, or put back in the queue.

* **Parameters:**
  **message_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [bool](https://docs.python.org/3/builtins/functions.html#bool)

<a id="eric_sse.queue_patterns.ReliableQueue.requeue_expired"></a>

#### requeue_expired()

Puts back in the queue messages not acknowledged within the visibility timeout. Returns how many.

* **Return type:**
  [int](https://docs.python.org/3/builtins/functions.html#int)

<a id="eric_sse.queue_patterns.ReliableQueue.in_flight"></a>

#### in_flight()

Popped messages not yet acknowledged.

* **Return type:**
  [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[*ReliableMessage*](#eric_sse.queue_patterns.ReliableMessage)]
