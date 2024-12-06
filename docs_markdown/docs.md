<a id="overview"></a>

# Overview

![image](_static/overview.png)

thanks a lot [https://excalidraw.com](https://excalidraw.com) !!

<a id="module-eric_sse.entities"></a>

<a id="entities"></a>

# Entities

<a id="eric_sse.entities.Message"></a>

### *class* Message(type: str, payload: dict | list | str | int | float | None = None)

Models a message

It’s just a container of information identified by a type.
For validation purposes you can override MessageQueueListener.on_message

<a id="eric_sse.entities.Message.type"></a>

#### type *: str*

<a id="eric_sse.entities.Message.payload"></a>

#### payload *: dict | list | str | int | float | None* *= None*

<a id="eric_sse.entities.SignedMessage"></a>

### *class* SignedMessage(sender_id: str, msg_type: str, msg_payload: dict | list | str | int | float | None = None)

A wrapper that adds sender id

<a id="eric_sse.entities.SignedMessage.type"></a>

#### *property* type

<a id="eric_sse.entities.SignedMessage.payload"></a>

#### *property* payload *: dict | list | str | int | float | None*

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

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Event handler. It executes when a message is delivered to client

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel(stream_delay_seconds: int = 0)

Base class for channels.

Provides functionalities for listeners and message delivery management. SSEChannel is the default implementation

<a id="eric_sse.entities.AbstractChannel.add_listener"></a>

#### add_listener() → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

Add the default listener

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener))

Adds a listener to channel

<a id="eric_sse.entities.AbstractChannel.remove_listener"></a>

#### remove_listener(l_id: str)

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(listener_id: str) → [Message](#eric_sse.entities.Message)

Returns next message for given listener id.

Raises a NoMessagesException if queue is empty

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(listener_id: str, msg: [Message](#eric_sse.entities.Message))

Adds a message to listener’s queue

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg: [Message](#eric_sse.entities.Message))

Enqueue a message to all listeners

<a id="eric_sse.entities.AbstractChannel.get_listener"></a>

#### get_listener(listener_id: str) → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg: [Message](#eric_sse.entities.Message)) → Any

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[Any]

Entry point for message streaming

In case of failure at channel resolution time, a special message with type=MESSAGE_TYPE_CLOSED is sent, and
correspondant listener is stopped

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch() → AsyncIterable[Any]

<a id="eric_sse.entities.AbstractChannel.notify_end"></a>

#### notify_end()

Broadcasts a MESSAGE_TYPE_CLOSED Message

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel(stream_delay_seconds: int = 0, retry_timeout_milliseconds: int = 5)

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

SSE streaming channel.
See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Currently, ‘id’ field is not supported.

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* DataProcessingChannel(max_workers: int, stream_delay_seconds: int = 0)

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

Channel intended for concurrent processing of data.

Relies on concurrent.futures.ThreadPoolExecutor.
Just override **adapt** method to control output returned to clients

MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[dict]

Launches the processing of the given listener’s queue

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener(channel: [AbstractChannel](#eric_sse.entities.AbstractChannel))

Bases: [`MessageQueueListener`](#eric_sse.entities.MessageQueueListener)

Listener for distrubuted applications

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.set_action"></a>

#### set_action(name: str, action: Callable[[[Message](#eric_sse.entities.Message)], list[[Message](#eric_sse.entities.Message)]])

Hooks a callable to a string key.

Callables are selected when listener processes the message depending on its type.

They should return a list of Messages corresponding to response to action requested.
Use ‘stop’ as Message type to stop receiver listener.

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_message"></a>

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Executes action correspondant to message’s type

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers-and-clients"></a>

# Prefab servers and clients

<a id="eric_sse.servers.SSEChannelContainer"></a>

### *class* SSEChannelContainer

Helper class for management of multiple SSE channels cases of use.

<a id="eric_sse.servers.SocketServer"></a>

### *class* SocketServer(file_descriptor_path: str)

An implementation of a socket server that acts as a controller to interact with library

**Accepted format**: a plain (no nested) JSON with the following keys:

``
"c": "channel id"
"v": "verb"
"t": "message type"
"p": "message payload"
``

Possible values of **verb** identifies a supported action:

``
"d" dispatch
"b" broadcast
"c" add listener
"l" listen (opens a stream)
"w" watch (opens a stream)
``

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
