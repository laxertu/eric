<a id="overview"></a>

# Overview

![image](_static/overview.png)

thanks a lot [https://excalidraw.com](https://excalidraw.com) !!

<a id="module-eric_sse.message"></a>

<a id="entities"></a>

# Entities

<a id="eric_sse.message.MessageContract"></a>

### *class* MessageContract

Bases: `ABC`

Contract class for messages

A message is just a container of information identified by a type.
For validation purposes you can override [`eric_sse.entities.MessageQueueListener.on_message`](#eric_sse.entities.MessageQueueListener.on_message)

<a id="eric_sse.message.MessageContract.type"></a>

#### *abstract property* type *: str*

Message type

<a id="eric_sse.message.MessageContract.payload"></a>

#### *abstract property* payload *: dict | list | str | int | float | None*

Message payload

<a id="eric_sse.message.Message"></a>

### *class* Message(msg_type: str, msg_payload: dict | list | str | int | float | None = None)

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Models a simple message

<a id="eric_sse.message.Message.type"></a>

#### *property* type *: str*

Message type

<a id="eric_sse.message.Message.payload"></a>

#### *property* payload *: dict | list | str | int | float | None*

Message payload

<a id="eric_sse.message.UniqueMessage"></a>

### *class* UniqueMessage(message_id: str, message: [MessageContract](#eric_sse.message.MessageContract), sender_id: str | None = None)

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Messages plus an unique identifier

<a id="eric_sse.message.UniqueMessage.id"></a>

#### *property* id *: str*

Unique message identifier

<a id="eric_sse.message.UniqueMessage.type"></a>

#### *property* type *: str*

Message type

<a id="eric_sse.message.UniqueMessage.sender_id"></a>

#### *property* sender_id *: str*

Returns the id of the listener that sent the message

<a id="eric_sse.message.UniqueMessage.payload"></a>

#### *property* payload *: dict*

Message payload

Returns a dictionary like:

```default
{
    "id": "message id",
    "sender_id": "sender id",
    "type": "message type",
    "payload": "original payload"
}
```

<a id="eric_sse.message.SignedMessage"></a>

### *class* SignedMessage(sender_id: str, msg_type: str, msg_payload: dict | list | str | int | float | None = None)

Bases: [`Message`](#eric_sse.message.Message)

Message plus sender id

<a id="eric_sse.message.SignedMessage.sender_id"></a>

#### *property* sender_id *: str*

Returns the id of the listener that sent the message

<a id="eric_sse.message.SignedMessage.payload"></a>

#### *property* payload *: dict*

Message payload
Returns a dictionary like:

```default
{
    "sender_id": "sender id",
    "type": "message type",
    "payload": "original payload"
}
```

<a id="module-eric_sse.entities"></a>

<a id="channels-and-listeners"></a>

# Channels and listeners

<a id="eric_sse.entities.MessageQueueListener"></a>

### *class* MessageQueueListener

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.entities.MessageQueueListener.start"></a>

#### *async* start() → None

<a id="eric_sse.entities.MessageQueueListener.start_sync"></a>

#### start_sync() → None

<a id="eric_sse.entities.MessageQueueListener.is_running"></a>

#### *async* is_running() → bool

<a id="eric_sse.entities.MessageQueueListener.is_running_sync"></a>

#### is_running_sync() → bool

<a id="eric_sse.entities.MessageQueueListener.stop"></a>

#### *async* stop() → None

<a id="eric_sse.entities.MessageQueueListener.stop_sync"></a>

#### stop_sync() → None

<a id="eric_sse.entities.MessageQueueListener.on_message"></a>

#### on_message(msg: [MessageContract](#eric_sse.message.MessageContract)) → None

Event handler. It executes when a message is delivered to client

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel(stream_delay_seconds: int = 0, queues_factory: [AbstractMessageQueueFactory](#eric_sse.queue.AbstractMessageQueueFactory) | None = None)

Base class for channels.

Provides functionalities for listeners and message delivery management.

[`eric_sse.queue.InMemoryMessageQueueFactory`](#eric_sse.queue.InMemoryMessageQueueFactory) is the default implementation used for queues_factory
see [`eric_sse.prefabs.SSEChannel`](#eric_sse.prefabs.SSEChannel)

* **Parameters:**
  * **stream_delay_seconds** (*int*) – Wait time in seconds between message delivery.
  * **queues_factory** ([*eric_sse.queue.AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory))

<a id="eric_sse.entities.AbstractChannel.add_listener"></a>

#### add_listener() → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

Add the default listener

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener))

Adds a listener to channel

<a id="eric_sse.entities.AbstractChannel.remove_listener"></a>

#### remove_listener(l_id: str)

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(listener_id: str) → [MessageContract](#eric_sse.message.MessageContract)

Returns next message for given listener id.

Raises a NoMessagesException if queue is empty

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(listener_id: str, msg: [MessageContract](#eric_sse.message.MessageContract))

Adds a message to listener’s queue

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg: [MessageContract](#eric_sse.message.MessageContract))

Enqueue a message to all listeners

<a id="eric_sse.entities.AbstractChannel.get_listener"></a>

#### get_listener(listener_id: str) → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg: [MessageContract](#eric_sse.message.MessageContract)) → Any

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[Any]

Entry point for message streaming

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch() → AsyncIterable[Any]

<a id="eric_sse.entities.AbstractChannel.notify_end"></a>

#### notify_end()

Broadcasts a MESSAGE_TYPE_CLOSED Message

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel(stream_delay_seconds: int = 0, retry_timeout_milliseconds: int = 5, queues_factory: [AbstractMessageQueueFactory](#eric_sse.queue.AbstractMessageQueueFactory) | None = None)

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

SSE streaming channel.
See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Currently, ‘id’ field is not supported.

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **retry_timeout_milliseconds** (*int*)
  * **queues_factory** ([*eric_sse.queue.AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory))

<a id="eric_sse.prefabs.SSEChannel.adapt"></a>

#### adapt(msg: [MessageContract](#eric_sse.message.MessageContract)) → dict

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* DataProcessingChannel(max_workers: int, stream_delay_seconds: int = 0)

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

Channel intended for concurrent processing of data.

Relies on [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor).
Just override **adapt** method to control output returned to clients

MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[dict]

Launches the processing of the given listener’s queue

<a id="eric_sse.prefabs.DataProcessingChannel.adapt"></a>

#### adapt(msg: [Message](#eric_sse.message.Message)) → dict

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener(channel: [AbstractChannel](#eric_sse.entities.AbstractChannel))

Bases: [`MessageQueueListener`](#eric_sse.entities.MessageQueueListener)

Listener for distributed applications

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.set_action"></a>

#### set_action(name: str, action: Callable[[[MessageContract](#eric_sse.message.MessageContract)], list[[MessageContract](#eric_sse.message.MessageContract)]])

Hooks a callable to a string key.

Callables are selected when listener processes the message depending on its type.

They should return a list of Messages corresponding to response to action requested.

Reserved actions are ‘start’, ‘stop’, ‘remove’.
Receiving a message with one of these types will fire correspondant action.

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.dispatch_to"></a>

#### dispatch_to(receiver: [MessageQueueListener](#eric_sse.entities.MessageQueueListener), msg: [MessageContract](#eric_sse.message.MessageContract))

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_message"></a>

#### on_message(msg: [SignedMessage](#eric_sse.message.SignedMessage)) → None

Executes action correspondant to message’s type

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.remove_sync"></a>

#### remove_sync()

Stop and unregister

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers-and-clients"></a>

# Prefab servers and clients

<a id="eric_sse.servers.SSEChannelContainer"></a>

### *class* SSEChannelContainer

Helper class for management of multiple SSE channels cases of use.

<a id="eric_sse.servers.SocketServer"></a>

### *class* SocketServer(file_descriptor_path: str)

An implementation of a socket server that acts as a controller to interact with library

**Accepted format**: a plain JSON with the following keys:

```default
{        
    "c": "channel id" 
    "v": "verb" 
    "t": "message type" 
    "p": "message payload" 
    "r": "receiver (listener id when verb is 'rl')"
}
```

Possible values of **verb** identifies a supported action:

```default
"d" dispatch
"b" broadcast
"c" create channel
"r" add listener
"l" listen (opens a stream)
"w" watch (opens a stream)
"rl" remove a listener
"rc" remove a channel
```

See examples

<a id="eric_sse.servers.SocketServer.shutdown"></a>

#### *async* shutdown()

Graceful Shutdown

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path: str)

Shortcut to start a server

<a id="module-eric_sse.clients"></a>

<a id="eric_sse.clients.SocketClient"></a>

### *class* SocketClient(file_descriptor_path: str)

A little facade to interact with SocketServer

<a id="eric_sse.clients.SocketClient.send_payload"></a>

#### *async* send_payload(payload: dict)

Send an arbitrary payload to a socket

see [`eric_sse.servers.SocketServer`](#eric_sse.servers.SocketServer)

<a id="eric_sse.clients.SocketClient.create_channel"></a>

#### *async* create_channel() → str

<a id="eric_sse.clients.SocketClient.register"></a>

#### *async* register(channel_id: str)

<a id="eric_sse.clients.SocketClient.stream"></a>

#### *async* stream(channel_id, listener_id) → AsyncIterable[str]

<a id="eric_sse.clients.SocketClient.broadcast_message"></a>

#### *async* broadcast_message(channel_id: str, message_type: str, payload: str | dict | int | float)

<a id="eric_sse.clients.SocketClient.dispatch"></a>

#### *async* dispatch(channel_id: str, receiver_id: str, message_type: str, payload: str | dict | int | float)

<a id="eric_sse.clients.SocketClient.remove_listener"></a>

#### *async* remove_listener(channel_id: str, listener_id: str)

<a id="eric_sse.clients.SocketClient.remove_channel"></a>

#### *async* remove_channel(channel_id: str)

<a id="module-eric_sse.queue"></a>

<a id="queues"></a>

# Queues

<a id="eric_sse.queue.Queue"></a>

### *class* Queue

Bases: `ABC`

Abstract base class for queues (FIFO)

<a id="eric_sse.queue.Queue.pop"></a>

#### *abstract* pop() → [MessageContract](#eric_sse.message.MessageContract)

Next message from the queue.

Raises a [`eric_sse.exception.NoMessagesException`](#eric_sse.exception.NoMessagesException) if the queue is empty.

<a id="eric_sse.queue.Queue.push"></a>

#### *abstract* push(message: [MessageContract](#eric_sse.message.MessageContract)) → None

<a id="eric_sse.queue.Queue.delete"></a>

#### *abstract* delete() → None

Removes all messages from the queue.

<a id="eric_sse.queue.AbstractMessageQueueFactory"></a>

### *class* AbstractMessageQueueFactory

Bases: `ABC`

Abstraction for queues creation

see [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.queue.AbstractMessageQueueFactory.create"></a>

#### *abstract* create() → [Queue](#eric_sse.queue.Queue)

<a id="eric_sse.queue.InMemoryMessageQueueFactory"></a>

### *class* InMemoryMessageQueueFactory

Bases: [`AbstractMessageQueueFactory`](#eric_sse.queue.AbstractMessageQueueFactory)

Default implementation used by [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.queue.InMemoryMessageQueueFactory.create"></a>

#### create() → [Queue](#eric_sse.queue.Queue)

<a id="eric_sse.queue.RepositoryError"></a>

### *exception* RepositoryError

Bases: `Exception`

Raised when an unexpected error occurs while trying to fetch messages from a queue.

Concrete implementations of [`Queue`](#eric_sse.queue.Queue) should wrap here the unexpected exceptions they catch before raising, and
an [`eric_sse.exception.NoMessagesException`](#eric_sse.exception.NoMessagesException) when a pop is requested on an empty queue.

<a id="module-eric_sse.exception"></a>

<a id="exceptions"></a>

# Exceptions

<a id="eric_sse.exception.InvalidChannelException"></a>

### *exception* InvalidChannelException

<a id="eric_sse.exception.InvalidListenerException"></a>

### *exception* InvalidListenerException

<a id="eric_sse.exception.InvalidMessageFormat"></a>

### *exception* InvalidMessageFormat

<a id="eric_sse.exception.NoMessagesException"></a>

### *exception* NoMessagesException

Raised when trying to fetch from an empty queue
