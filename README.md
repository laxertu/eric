<a id="the-lightweight-library-for-async-messaging-nobody-expects"></a>

# The lightweight library for async messaging nobody expects.

Features

* Send to one listener and broadcast
* SSE format was adopted by design, is order to make library suitable for such kind of model
* Sockets
* Callbacks
* Threading support for large data processing

Possible applications

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See [https://github.com/laxertu/eric-api](https://github.com/laxertu/eric-api)

Trivia

Library name pretends to be a tribute to the following movie [https://en.wikipedia.org/wiki/Looking_for_Eric](https://en.wikipedia.org/wiki/Looking_for_Eric)

<a id="module-eric_sse.entities"></a>

<a id="entities"></a>

# Entities

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* eric_sse.entities.AbstractChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

Base class for channels.

Provides functionalities for listeners and message delivery management.
SSEChannel is the default implementation

<a id="eric_sse.entities.AbstractChannel.add_listener"></a>

#### add_listener() → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

Add the default listener

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg: [Message](#eric_sse.entities.Message))

Enqueue a message to all listeners

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(listener_id: str) → [Message](#eric_sse.entities.Message)

Returns next message for given listener id.
Raises a NoMessagesException if queue is empty

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(listener_id: str, msg: [Message](#eric_sse.entities.Message))

Adds a message to listener’s queue

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[dict]

Entry point for message streamiong

In case of failure at channel resulution time, a special message with type=MESSAGE_TYPE_CLOSED is sent, and
correspondant listener is stopped

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener))

Adds a listener to channel

<a id="eric_sse.entities.Message"></a>

### *class* eric_sse.entities.Message(type: str, payload: dict | list | str | int | float | None = None)

Models a message

It’s just a container of information identified by a type.
For validation purposes you can override MessageQueueListener.on_message

<a id="eric_sse.entities.MessageQueueListener"></a>

### *class* eric_sse.entities.MessageQueueListener

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.entities.MessageQueueListener.on_message"></a>

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Event handler. It executes whan a message is delivered to client

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* eric_sse.prefabs.DataProcessingChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

Channel that invokes a callable in a Pool of threads

<a id="eric_sse.prefabs.DataProcessingChannel.add_threaded_listener"></a>

#### add_threaded_listener(callback: Callable, max_workers: int) → [ThreadPoolListener](#eric_sse.prefabs.ThreadPoolListener)

Adds a threaded listener

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* eric_sse.prefabs.SSEChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

SSE streaming channel.

See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)
Currently, ‘id’ field is not supported.

<a id="eric_sse.prefabs.ThreadPoolListener"></a>

### *class* eric_sse.prefabs.ThreadPoolListener(callback: Callable, max_workers: int)

Listener intended for concurrent processing of data.

Relies on concurrent.futures.ThreadPoolExecutor.

MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

Note that:

> * same callback is invoked, no matter of message type
> * callback execution order is not guaranteed (to be the same as the one while dispatching to channel)

<a id="eric_sse.prefabs.ThreadPoolListener.on_message"></a>

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Event handler. It executes whan a message is delivered to client

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers"></a>

# Prefab servers

<a id="eric_sse.servers.ChannelContainer"></a>

### *class* eric_sse.servers.ChannelContainer

Helper class for managment of multiple SSE channels cases of use.

<a id="eric_sse.servers.SocketServer"></a>

### *class* eric_sse.servers.SocketServer(file_descriptor_path: str)

An implementation of a socket server that reveives and broadcasts automatically all messages that receives

A static shortcut for starting a basic server is provided. See examples.

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path: str)

Shortcut to start a server

<a id="module-eric_sse.exception"></a>

<a id="exceptions"></a>

# Exceptions

<a id="eric_sse.exception.InvalidChannelException"></a>

### *exception* eric_sse.exception.InvalidChannelException

<a id="eric_sse.exception.InvalidListenerException"></a>

### *exception* eric_sse.exception.InvalidListenerException

<a id="eric_sse.exception.InvalidMessageFormat"></a>

### *exception* eric_sse.exception.InvalidMessageFormat

<a id="eric_sse.exception.NoMessagesException"></a>

### *exception* eric_sse.exception.NoMessagesException

Raised when trying to fetch from an empty queue
