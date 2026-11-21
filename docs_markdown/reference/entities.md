<a id="entities"></a>

# Entities

<a id="module-eric_sse.message"></a>

<a id="messages"></a>

## Messages

<a id="eric_sse.message.MessageContract"></a>

### *class* MessageContract

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Contract class for messages

A message is just a container of information identified by a type.
To validate messages, override [`before_dispatch()`](#eric_sse.entities.AbstractChannel.before_dispatch), or
[`on_message()`](#eric_sse.listener.MessageQueueListener.on_message) to check them on delivery.

<a id="eric_sse.message.MessageContract.type"></a>

#### *abstract property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.message.MessageContract.payload"></a>

#### *abstract property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.message.MessageContract.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Optional message identifier, e.g. the “id” field of an SSE event. None if the message has none.

<a id="eric_sse.message.M"></a>

### *class* M

Type of messages handled by generic queues and listeners.

alias of TypeVar(‘M’, bound=[`MessageContract`](#eric_sse.message.MessageContract))

<a id="eric_sse.message.MIn"></a>

### *class* MIn

Type of messages pushed to a queue, or dispatched to a channel.

alias of TypeVar(‘MIn’, bound=[`MessageContract`](#eric_sse.message.MessageContract))

<a id="eric_sse.message.MOut"></a>

### *class* MOut

Type of messages popped from a queue, or delivered by a channel.

alias of TypeVar(‘MOut’, bound=[`MessageContract`](#eric_sse.message.MessageContract))

<a id="eric_sse.message.Message"></a>

### *class* Message

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Models a simple message

* **Parameters:**
  * **msg_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Message type.
  * **msg_payload** – Message payload.
  * **msg_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Optional message identifier, see [`id`](#eric_sse.message.MessageContract.id).

<a id="eric_sse.message.Message.__init__"></a>

#### \_\_init_\_(msg_type, msg_payload=None, msg_id=None)

* **Parameters:**
  * **msg_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_payload** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *|* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)
  * **msg_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)
* **Return type:**
  None

<a id="eric_sse.message.Message.type"></a>

#### *property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.message.Message.payload"></a>

#### *property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.message.Message.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Optional message identifier, e.g. the “id” field of an SSE event. None if the message has none.

<a id="eric_sse.message.SignedMessage"></a>

### *class* SignedMessage

Bases: [`Message`](#eric_sse.message.Message)

Message plus sender id

<a id="eric_sse.message.SignedMessage.__init__"></a>

#### \_\_init_\_(sender_id, msg_type, msg_payload=None, msg_id=None)

* **Parameters:**
  * **sender_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_payload** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *|* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)
  * **msg_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)

<a id="eric_sse.message.SignedMessage.sender_id"></a>

#### *property* sender_id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Returns the id of the listener that sent the message

<a id="module-eric_sse.entities"></a>

<a id="channels-and-connections"></a>

## Channels and connections

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC), [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[[`MIn`](#eric_sse.message.MIn), [`MOut`](#eric_sse.message.MOut)]

Base class for channels.

Provides functionalities for connections and message delivery management. A connection pairs a listener with its
queue, and its id is the address messages are dispatched to, see [`Connection`](#eric_sse.connection.Connection).

Generic on the type of messages it dispatches (**MIn**) and delivers (**MOut**), e.g.
`SSEChannel[SignedMessage, SignedMessage]`, as its queues are `Queue[MIn, MOut]` and its listeners
`MessageQueueListener[MOut]`. They differ when queues transform messages, e.g.
`SSEChannel[MessageContract, ReliableMessage]` with [`ReliableQueue`](queue_patterns.md#eric_sse.queue_patterns.ReliableQueue) queues.
Plain channels handle any message.

[`InMemoryConnectionsFactory`](#eric_sse.connection.InMemoryConnectionsFactory) is the default implementation used for **connections_factory** parameter.

see [`SSEChannel`](prefabs.md#eric_sse.prefabs.SSEChannel)

**Hooks**: subclasses can override [`on_connection_added()`](#eric_sse.entities.AbstractChannel.on_connection_added), [`on_connection_removed()`](#eric_sse.entities.AbstractChannel.on_connection_removed),
[`on_stream_start()`](#eric_sse.entities.AbstractChannel.on_stream_start), [`on_stream_end()`](#eric_sse.entities.AbstractChannel.on_stream_end), [`on_wait_timeout()`](#eric_sse.entities.AbstractChannel.on_wait_timeout), [`before_dispatch()`](#eric_sse.entities.AbstractChannel.before_dispatch) and [`on_error()`](#eric_sse.entities.AbstractChannel.on_error).
They do nothing by default.

**Error handlers**: errors raised by queues and listeners are passed to the handlers registered with
[`add_queuing_error_handler()`](#eric_sse.entities.AbstractChannel.add_queuing_error_handler) and [`add_listener_error_handler()`](#eric_sse.entities.AbstractChannel.add_listener_error_handler).
Then they are either re-raised or, when the channel swallows them, logged.
Control flow exceptions, like [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException), are neither logged nor handled.

* **Parameters:**
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Pause in seconds after each message delivered by [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream). Can be used to limit its rate.
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Optionally sets the channel id.
  * **connections_factory** ([*ConnectionsFactory*](#eric_sse.connection.ConnectionsFactory)) – Factory to be used for creating connections instances on channel subscriptions.

<a id="eric_sse.entities.AbstractChannel.wait_timeout_seconds"></a>

#### wait_timeout_seconds *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1.0*

How long [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) waits for a message before checking again whether its listener is running.

<a id="eric_sse.entities.AbstractChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, channel_id=None, connections_factory=None)

* **Parameters:**
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/builtins/functions.html#int))
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)
  * **connections_factory** ([*ConnectionsFactory*](#eric_sse.connection.ConnectionsFactory) *|* *None*)

<a id="eric_sse.entities.AbstractChannel.add_queuing_error_handler"></a>

#### add_queuing_error_handler(handler)

Registers a handler for errors raised by queues. Handlers are called in registration order, and are not persisted.

* **Parameters:**
  **handler** ([*QueuingErrorHandler*](handlers.md#eric_sse.handlers.QueuingErrorHandler))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.add_listener_error_handler"></a>

#### add_listener_error_handler(handler)

Registers a handler for errors raised by listeners. Handlers are called in registration order, and are not persisted.

* **Parameters:**
  **handler** ([*ListenerErrorHandler*](handlers.md#eric_sse.handlers.ListenerErrorHandler))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel._pop_next"></a>

#### \_pop_next(connection_id)

Pops the next message of given connection, without notifying its listener: the first half of
[`deliver_next()`](#eric_sse.entities.AbstractChannel.deliver_next), for subclasses that notify listeners their own way, e.g. in an executor.
Then they must pass listener errors to [`_on_listener_error()`](#eric_sse.entities.AbstractChannel._on_listener_error).

Raises as [`deliver_next()`](#eric_sse.entities.AbstractChannel.deliver_next) does. Queue errors are re-raised after error handlers.

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*MOut*](#eric_sse.message.MOut)

<a id="eric_sse.entities.AbstractChannel._on_listener_error"></a>

#### \_on_listener_error(connection_id, msg, exception)

Logs an error raised by a listener’s `on_message`, and passes it to error handlers.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MOut*](#eric_sse.message.MOut))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Unique identifier for this channel, it can be set by **channel_id** constructor parameter

<a id="eric_sse.entities.AbstractChannel.to_dict"></a>

#### to_dict()

Channel configuration to be persisted. Keys must be constructor parameters, see [`from_dict()`](#eric_sse.entities.AbstractChannel.from_dict).

Subclasses with additional configuration should extend it:

```default
def to_dict(self) -> dict:
    return {**super().to_dict(), 'my_param': self.my_param}
```

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.entities.AbstractChannel.from_dict"></a>

#### *classmethod* from_dict(data, connections_factory=None)

Builds a channel from a [`to_dict()`](#eric_sse.entities.AbstractChannel.to_dict) representation. Override it if constructor parameters don’t match **data** keys.

* **Parameters:**
  * **data** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict)) – Constructor parameters, except **connections_factory**.
  * **connections_factory** ([*ConnectionsFactory*](#eric_sse.connection.ConnectionsFactory))
* **Return type:**
   *\_Channel*

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg)

Models output of channel streams

* **Parameters:**
  **msg** ([*MOut*](#eric_sse.message.MOut))
* **Return type:**
  [*Any*](https://docs.python.org/3/library/typing.html#typing.Any)

<a id="eric_sse.entities.AbstractChannel.adapt_error"></a>

#### *abstract* adapt_error(exception)

Models errors in channel streams, see [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream).

**exception** is safe to expose to clients: unexpected errors are replaced by an
[`InternalStreamError`](exceptions.md#eric_sse.exception.InternalStreamError), that hides their details.

* **Parameters:**
  **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  [*Any*](https://docs.python.org/3/library/typing.html#typing.Any)

<a id="eric_sse.entities.AbstractChannel.on_connection_added"></a>

#### on_connection_added(connection)

Hook called by [`add_connection()`](#eric_sse.entities.AbstractChannel.add_connection) and [`register_listener()`](#eric_sse.entities.AbstractChannel.register_listener).

Not called when connections are registered with [`register_connection()`](#eric_sse.entities.AbstractChannel.register_connection), e.g. when a channel is
loaded from persistence, because that’s not a new subscription.

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_connection_removed"></a>

#### on_connection_removed(connection)

Hook called by `remove_connection()`, after the connection has been removed.

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_stream_start"></a>

#### on_stream_start(connection)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) starts, after the listener has been started.

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_stream_end"></a>

#### on_stream_end(connection)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) ends, for any reason: listener stopped, error, or client disconnection.

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.before_dispatch"></a>

#### before_dispatch(connection_id, msg)

Hook called by [`dispatch()`](#eric_sse.entities.AbstractChannel.dispatch), and so by [`broadcast()`](#eric_sse.entities.AbstractChannel.broadcast) for each connection, before enqueuing **msg**.

* **Returns:**
  The message to enqueue, possibly a different one, or None to drop it.
* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MIn*](#eric_sse.message.MIn))
* **Return type:**
  [*MIn*](#eric_sse.message.MIn) | None

<a id="eric_sse.entities.AbstractChannel.on_wait_timeout"></a>

#### on_wait_timeout(connection)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) waited [`wait_timeout_seconds`](#eric_sse.entities.AbstractChannel.wait_timeout_seconds) for a message and none arrived.

It is not an error: an idle stream times out periodically, to check whether its listener is still running.
Can be used, for example, to collect metrics or to end idle streams by stopping their listener.

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_error"></a>

#### on_error(connection, exception)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) catches an unexpected exception, before yielding an error.

By default, it goes on. The exception has already been logged, and, if raised by a queue, passed to error handlers.
The stream waits [`wait_timeout_seconds`](#eric_sse.entities.AbstractChannel.wait_timeout_seconds) before trying again, so a failing backend doesn’t make it spin.

* **Returns:**
  False to end the stream after the error.
* **Parameters:**
  * **connection** ([*Connection*](#eric_sse.connection.Connection))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  [bool](https://docs.python.org/3/builtins/functions.html#bool)

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(connection_id)

Entry point for message streaming. Starts the connection’s listener, and ends when it is stopped.

Waits for messages through [`wait_next()`](#eric_sse.entities.AbstractChannel.wait_next), so an idle stream doesn’t consume CPU.
A stopped listener is noticed at the latest after [`wait_timeout_seconds`](#eric_sse.entities.AbstractChannel.wait_timeout_seconds).

Errors are yielded through [`adapt_error()`](#eric_sse.entities.AbstractChannel.adapt_error). After an [`InvalidConnectionException`](exceptions.md#eric_sse.exception.InvalidConnectionException), an [`InvalidChannelException`](exceptions.md#eric_sse.exception.InvalidChannelException) or a [`StoppedListenerException`](exceptions.md#eric_sse.exception.StoppedListenerException), the stream ends.
Unexpected errors are logged and yielded as an [`InternalStreamError`](exceptions.md#eric_sse.exception.InternalStreamError), hiding
their details, and [`on_error()`](#eric_sse.entities.AbstractChannel.on_error) decides whether the stream goes on.

Calls [`on_stream_start()`](#eric_sse.entities.AbstractChannel.on_stream_start), [`on_wait_timeout()`](#eric_sse.entities.AbstractChannel.on_wait_timeout) and [`on_stream_end()`](#eric_sse.entities.AbstractChannel.on_stream_end) hooks.

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[*Any*](https://docs.python.org/3/library/typing.html#typing.Any)]

<a id="eric_sse.entities.AbstractChannel.add_connection"></a>

#### add_connection()

Creates a connection through the connections factory, and registers it.

* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(listener)

Creates a connection for an existing listener, and registers it.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener) *[*[*MOut*](#eric_sse.message.MOut) *]*)
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)

<a id="eric_sse.entities.AbstractChannel.register_connection"></a>

#### register_connection(connection)

Register and existing connection. [`add_connection()`](#eric_sse.entities.AbstractChannel.add_connection) and [`register_listener()`](#eric_sse.entities.AbstractChannel.register_listener) call it too,
so subclasses can override it to set up every new connection.

Calls [`on_registered()`](#eric_sse.listener.MessageQueueListener.on_registered) on the connection’s listener.

**Warning**: Listener and queue should belong to the same classes created by the connections factory (the connections repository, for channels built by a channel repository) to avoid compatibility issues with persistence layer

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(connection_id)

Returns next message of given connection.

Raises a [`StoppedListenerException`](exceptions.md#eric_sse.exception.StoppedListenerException) if the listener is not running, even if its
queue is empty, and a NoMessagesException if the queue is empty.
Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*MOut*](#eric_sse.message.MOut)

<a id="eric_sse.entities.AbstractChannel.wait_next"></a>

#### *async* wait_next(connection_id, timeout)

Waits up to **timeout** seconds for the next message of given connection, without blocking the event loop.

Raises a [`StoppedListenerException`](exceptions.md#eric_sse.exception.StoppedListenerException) if the listener is not running, as waiting for
messages that it won’t receive is not allowed, and a NoMessagesException if no message arrives in time.
Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float))
* **Return type:**
  [*MOut*](#eric_sse.message.MOut)

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(connection_id, msg)

Adds a message to the connection’s queue, unless [`before_dispatch()`](#eric_sse.entities.AbstractChannel.before_dispatch) drops it.

Queue errors are re-raised after error handlers.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MIn*](#eric_sse.message.MIn))

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg)

Enqueue a message to the connections registered when it starts. A queue error is logged, and doesn’t stop
delivery to the other ones. Hooks and error handlers can remove connections meanwhile.

* **Parameters:**
  **msg** ([*MIn*](#eric_sse.message.MIn))

<a id="eric_sse.entities.AbstractChannel.get_connection"></a>

#### get_connection(connection_id)

Raises an [`InvalidConnectionException`](exceptions.md#eric_sse.exception.InvalidConnectionException) if the channel has no such connection.

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch()

Streams channel messages through a new connection, removed when the stream ends:

```default
async for message in channel.watch():
    ...
```

* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[*Any*](https://docs.python.org/3/library/typing.html#typing.Any)]

<a id="module-eric_sse.connection"></a>

<a id="eric_sse.connection.Connection"></a>

### *class* Connection

Bases: [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[`L`, `Q`]

A connection is a listener and its related message queue.

It’s what channels and repositories identify: messages are dispatched to a connection id, and listeners and queues
have no identity of their own.

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*Queue*](#eric_sse.queues.Queue))

<a id="eric_sse.connection.Connection.__init__"></a>

#### \_\_init_\_(listener, queue, connection_id=None)

* **Parameters:**
  * **listener** (*L*)
  * **queue** (*Q*)
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)

<a id="eric_sse.connection.ConnectionsFactory"></a>

### *class* ConnectionsFactory

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC), [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[`L`, `Q`]

<a id="eric_sse.connection.ConnectionsFactory.create"></a>

#### *abstract* create(listener=None)

Creates a connection

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)) – If provided, assigns a concrete listener
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)[*L*, *Q*]

<a id="eric_sse.connection.InMemoryConnectionsFactory"></a>

### *class* InMemoryConnectionsFactory

Bases: [`ConnectionsFactory`](#eric_sse.connection.ConnectionsFactory)[[`MessageQueueListener`](#eric_sse.listener.MessageQueueListener), [`InMemoryQueue`](#eric_sse.queues.InMemoryQueue)]

Creates Connections with In memory queues (no persistence support)

<a id="eric_sse.connection.InMemoryConnectionsFactory.create"></a>

#### create(listener=None)

Creates a connection

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)) – If provided, assigns a concrete listener
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)[[*MessageQueueListener*](#eric_sse.listener.MessageQueueListener), [*InMemoryQueue*](#eric_sse.queues.InMemoryQueue)]

<a id="module-eric_sse.queues"></a>

<a id="queues"></a>

## Queues

<a id="eric_sse.queues.Queue"></a>

### *class* Queue

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC), [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[[`MIn`](#eric_sse.message.MIn), [`MOut`](#eric_sse.message.MOut)]

Abstract base class for queues (FIFO).

Generic on the type of messages pushed (**MIn**) and popped (**MOut**), e.g. `Queue[SignedMessage, SignedMessage]`.
They differ when a queue transforms messages, as [`ReliableQueue`](queue_patterns.md#eric_sse.queue_patterns.ReliableQueue) does.
Plain `Queue` holds any message.

Implementations must provide [`pop()`](#eric_sse.queues.Queue.pop) and [`push()`](#eric_sse.queues.Queue.push). Override [`wait_pop()`](#eric_sse.queues.Queue.wait_pop) too if the backend
can wait for messages without blocking a thread, as [`InMemoryQueue`](#eric_sse.queues.InMemoryQueue) does.

<a id="eric_sse.queues.Queue.pop"></a>

#### *abstract* pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*MOut*](#eric_sse.message.MOut)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available, after waiting
**timeout** seconds.

<a id="eric_sse.queues.Queue.push"></a>

#### *abstract* push(message)

* **Parameters:**
  **message** ([*MIn*](#eric_sse.message.MIn))
* **Return type:**
  None

<a id="eric_sse.queues.Queue.wait_pop"></a>

#### *async* wait_pop(timeout)

Waits for the next message without blocking the event loop.

The default implementation runs [`pop()`](#eric_sse.queues.Queue.pop) with **timeout** in a worker thread, so it takes one thread
per waiting call. Override it with a native async wait when possible.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message.
* **Return type:**
  [*MOut*](#eric_sse.message.MOut)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="eric_sse.queues.InMemoryQueue"></a>

### *class* InMemoryQueue

Bases: [`Queue`](#eric_sse.queues.Queue)[[`M`](#eric_sse.message.M), [`M`](#eric_sse.message.M)]

In memory implementation. Not durable: its messages live in the current process only.

It has a single consumer, as a queue belongs to one listener: concurrent [`wait_pop()`](#eric_sse.queues.InMemoryQueue.wait_pop) calls on the same
queue are not supported. [`wait_pop()`](#eric_sse.queues.InMemoryQueue.wait_pop) waits natively, without threads or polling.
[`push()`](#eric_sse.queues.InMemoryQueue.push) can be called from any thread.

It can’t be serialised (e.g. pickled), so it can only be persisted with storages that keep objects
in process, such as [`InMemoryStorage`](persistence.md#eric_sse.repository.InMemoryStorage).

<a id="eric_sse.queues.InMemoryQueue.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.queues.InMemoryQueue.pop"></a>

#### pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*M*](#eric_sse.message.M)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available, after waiting
**timeout** seconds.

<a id="eric_sse.queues.InMemoryQueue.push"></a>

#### push(message)

* **Parameters:**
  **message** ([*M*](#eric_sse.message.M))
* **Return type:**
  None

<a id="eric_sse.queues.InMemoryQueue.wait_pop"></a>

#### *async* wait_pop(timeout)

Waits for the next message without blocking the event loop.

The default implementation runs [`pop()`](#eric_sse.queues.InMemoryQueue.pop) with **timeout** in a worker thread, so it takes one thread
per waiting call. Override it with a native async wait when possible.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message.
* **Return type:**
  [*M*](#eric_sse.message.M)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="module-eric_sse.listener"></a>

<a id="listeners"></a>

## Listeners

<a id="eric_sse.listener.MessageQueueListener"></a>

### *class* MessageQueueListener

Bases: [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[[`M`](#eric_sse.message.M)]

Base class for listeners.

Generic on the type of messages it handles, e.g. `MessageQueueListener[SignedMessage]`. Plain
`MessageQueueListener` handles any message.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.listener.MessageQueueListener.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.listener.MessageQueueListener.on_registered"></a>

#### on_registered(channel, connection_id)

Hook called when the listener is registered to **channel**, through connection **connection_id**, see
[`register_connection()`](#eric_sse.entities.AbstractChannel.register_connection). Also called when a channel is loaded from
persistence. Does nothing by default: override it if the listener needs its channel or its address, e.g. to
dispatch messages.

* **Parameters:**
  * **channel** ([*AbstractChannel*](#eric_sse.entities.AbstractChannel) *[**Any* *,* [*M*](#eric_sse.message.M) *]*)
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  None

<a id="eric_sse.listener.MessageQueueListener.on_message"></a>

#### on_message(msg)

Event handler. It executes when a message is delivered to client

* **Parameters:**
  **msg** ([*M*](#eric_sse.message.M))
* **Return type:**
  None

<a id="eric_sse.listener.MessageQueueListener.start"></a>

#### start()

* **Return type:**
  None

<a id="eric_sse.listener.MessageQueueListener.stop"></a>

#### stop()

* **Return type:**
  None

<a id="eric_sse.listener.MessageQueueListener.is_running"></a>

#### is_running()

* **Return type:**
  [bool](https://docs.python.org/3/builtins/functions.html#bool)
