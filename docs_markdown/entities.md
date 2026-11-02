<a id="entities"></a>

# Entities

<a id="module-eric_sse.message"></a>

<a id="messages"></a>

# Messages

<a id="eric_sse.message.MessageContract"></a>

### *class* MessageContract

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Contract class for messages

A message is just a container of information identified by a type.
For validation purposes you can override its [`on_message()`](#eric_sse.listener.MessageQueueListener.on_message) method.

<a id="eric_sse.message.MessageContract.type"></a>

#### *abstract property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.message.MessageContract.payload"></a>

#### *abstract property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.message.Message"></a>

### *class* Message

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Models a simple message

<a id="eric_sse.message.Message.__init__"></a>

#### \_\_init_\_(msg_type, msg_payload=None)

* **Parameters:**
  * **msg_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_payload** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *|* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)
* **Return type:**
  None

<a id="eric_sse.message.Message.type"></a>

#### *property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.message.Message.payload"></a>

#### *property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.message.UniqueMessage"></a>

### *class* UniqueMessage

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Messages plus an unique identifier

<a id="eric_sse.message.UniqueMessage.__init__"></a>

#### \_\_init_\_(message, sender_id=None, message_id=None)

* **Parameters:**
  * **message** ([*MessageContract*](#eric_sse.message.MessageContract))
  * **sender_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)
  * **message_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)
* **Return type:**
  None

<a id="eric_sse.message.UniqueMessage.id"></a>

#### *property* id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Unique message identifier

<a id="eric_sse.message.UniqueMessage.type"></a>

#### *property* type *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Message type

<a id="eric_sse.message.UniqueMessage.sender_id"></a>

#### *property* sender_id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Returns the id of the listener that sent the message

<a id="eric_sse.message.UniqueMessage.payload"></a>

#### *property* payload *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict) | [list](https://docs.python.org/3/builtins/stdtypes.html#list) | [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [int](https://docs.python.org/3/builtins/functions.html#int) | [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Message payload

<a id="eric_sse.message.SignedMessage"></a>

### *class* SignedMessage

Bases: [`Message`](#eric_sse.message.Message)

Message plus sender id

<a id="eric_sse.message.SignedMessage.__init__"></a>

#### \_\_init_\_(sender_id, msg_type, msg_payload=None)

* **Parameters:**
  * **sender_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg_payload** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *|* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)

<a id="eric_sse.message.SignedMessage.sender_id"></a>

#### *property* sender_id *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Returns the id of the listener that sent the message

<a id="module-eric_sse.entities"></a>

<a id="channels-and-connections"></a>

# Channels and connections

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Base class for channels.

Provides functionalities for listeners and message delivery management.

[`InMemoryConnectionsFactory`](#eric_sse.connection.InMemoryConnectionsFactory) is the default implementation used for **connections_factory** parameter.

see [`SSEChannel`](prefabs.md#eric_sse.prefabs.SSEChannel)

**Hooks**: subclasses can override [`on_listener_added()`](#eric_sse.entities.AbstractChannel.on_listener_added), [`on_listener_removed()`](#eric_sse.entities.AbstractChannel.on_listener_removed),
[`on_stream_start()`](#eric_sse.entities.AbstractChannel.on_stream_start), [`on_stream_end()`](#eric_sse.entities.AbstractChannel.on_stream_end), [`before_dispatch()`](#eric_sse.entities.AbstractChannel.before_dispatch) and [`on_error()`](#eric_sse.entities.AbstractChannel.on_error).
They do nothing by default.

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
  [*AbstractChannel*](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg)

Models output of channel streams

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  [*Any*](https://docs.python.org/3/library/typing.html#typing.Any)

<a id="eric_sse.entities.AbstractChannel.on_listener_added"></a>

#### on_listener_added(listener)

Hook called by [`add_listener()`](#eric_sse.entities.AbstractChannel.add_listener) and [`register_listener()`](#eric_sse.entities.AbstractChannel.register_listener).

Not called when connections are registered with [`register_connection()`](#eric_sse.entities.AbstractChannel.register_connection), e.g. when a channel is
loaded from persistence, because that’s not a new subscription.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_listener_removed"></a>

#### on_listener_removed(listener)

Hook called by `remove_listener()`, after the listener has been removed.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_stream_start"></a>

#### on_stream_start(listener)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) starts, after the listener has been started.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.on_stream_end"></a>

#### on_stream_end(listener)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) ends, for any reason: listener stopped, error, or client disconnection.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel.before_dispatch"></a>

#### before_dispatch(listener_id, msg)

Hook called by [`dispatch()`](#eric_sse.entities.AbstractChannel.dispatch), and so by [`broadcast()`](#eric_sse.entities.AbstractChannel.broadcast) for each listener, before enqueuing **msg**.

* **Returns:**
  The message to enqueue, possibly a different one, or None to drop it.
* **Parameters:**
  * **listener_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract) | None

<a id="eric_sse.entities.AbstractChannel.on_error"></a>

#### on_error(listener, exception)

Hook called when [`message_stream()`](#eric_sse.entities.AbstractChannel.message_stream) catches an unexpected exception, before yielding an ‘error’ message.

By default it logs the exception and goes on.
The stream waits [`wait_timeout_seconds`](#eric_sse.entities.AbstractChannel.wait_timeout_seconds) before trying again, so a failing backend doesn’t make it spin.

* **Returns:**
  False to end the stream after the ‘error’ message.
* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  [bool](https://docs.python.org/3/builtins/functions.html#bool)

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener)

Entry point for message streaming. Starts **listener**, and ends when it is stopped.

Waits for messages through [`wait_next()`](#eric_sse.entities.AbstractChannel.wait_next), so an idle stream doesn’t consume CPU.
A stopped listener is noticed at the latest after [`wait_timeout_seconds`](#eric_sse.entities.AbstractChannel.wait_timeout_seconds).

Errors are yield as messages of type ‘error’. Their payload is serialisable: for an invalid listener or
channel it’s a dict with ‘error’ (exception class name) and ‘message’ keys, and the stream ends;
for unexpected errors it’s None, and [`on_error()`](#eric_sse.entities.AbstractChannel.on_error) decides whether the stream goes on.

Calls [`on_stream_start()`](#eric_sse.entities.AbstractChannel.on_stream_start) and [`on_stream_end()`](#eric_sse.entities.AbstractChannel.on_stream_end) hooks.

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[*Any*](https://docs.python.org/3/library/typing.html#typing.Any)]

<a id="eric_sse.entities.AbstractChannel.add_listener"></a>

#### add_listener()

Shortcut that creates a connection and returns correspondant listener

* **Return type:**
  [*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(listener)

Registers an existing listener

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))

<a id="eric_sse.entities.AbstractChannel.register_connection"></a>

#### register_connection(connection)

Register and existing connection. [`add_listener()`](#eric_sse.entities.AbstractChannel.add_listener) and [`register_listener()`](#eric_sse.entities.AbstractChannel.register_listener) call it too,
so subclasses can override it to set up every new connection.

**Warning**: Listener and queue should belong to the same classes created by the connections factory (the connections repository, for channels built by a channel repository) to avoid compatibility issues with persistence layer

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(listener_id)

Returns next message for given listener id.

Raises a NoMessagesException if queue is empty

* **Parameters:**
  **listener_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.entities.AbstractChannel.wait_next"></a>

#### *async* wait_next(listener_id, timeout)

Waits up to **timeout** seconds for the next message for given listener id, without blocking the event loop.

Raises a NoMessagesException if the listener is not running or no message arrives in time.

* **Parameters:**
  * **listener_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float))
* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(listener_id, msg)

Adds a message to listener’s queue, unless [`before_dispatch()`](#eric_sse.entities.AbstractChannel.before_dispatch) drops it.

* **Parameters:**
  * **listener_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg)

Enqueue a message to all listeners

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch()

Streams channel messages through a new listener, removed when the stream ends:

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

A connection is just a listener and its related message queue

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

# Queues

<a id="eric_sse.queues.Queue"></a>

### *class* Queue

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Abstract base class for queues (FIFO).

Implementations must provide [`pop()`](#eric_sse.queues.Queue.pop) and [`push()`](#eric_sse.queues.Queue.push). Override [`wait_pop()`](#eric_sse.queues.Queue.wait_pop) too if the backend
can wait for messages without blocking a thread, as [`InMemoryQueue`](#eric_sse.queues.InMemoryQueue) does.

<a id="eric_sse.queues.Queue.pop"></a>

#### *abstract* pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available within **timeout**.

<a id="eric_sse.queues.Queue.push"></a>

#### *abstract* push(message)

* **Parameters:**
  **message** ([*MessageContract*](#eric_sse.message.MessageContract))
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
  [*MessageContract*](#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="eric_sse.queues.InMemoryQueue"></a>

### *class* InMemoryQueue

Bases: [`Queue`](#eric_sse.queues.Queue)

In memory implementation. Not durable: its messages live in the current process only.

[`wait_pop()`](#eric_sse.queues.InMemoryQueue.wait_pop) waits natively, without threads or polling. [`push()`](#eric_sse.queues.InMemoryQueue.push) can be called from any thread.

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
  [*MessageContract*](#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available within **timeout**.

<a id="eric_sse.queues.InMemoryQueue.push"></a>

#### push(message)

* **Parameters:**
  **message** ([*MessageContract*](#eric_sse.message.MessageContract))
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
  [*MessageContract*](#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="module-eric_sse.listener"></a>

<a id="listeners"></a>

# Listeners

<a id="eric_sse.listener.MessageQueueListener"></a>

### *class* MessageQueueListener

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.listener.MessageQueueListener.__init__"></a>

#### \_\_init_\_(listener_id=None)

* **Parameters:**
  **listener_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)

<a id="eric_sse.listener.MessageQueueListener.on_message"></a>

#### on_message(msg)

Event handler. It executes when a message is delivered to client

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
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
