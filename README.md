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

# Entities

### *class* eric_sse.entities.AbstractChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

Base class for channels.

Provides functionalities for listeners and message delivery management.
SSEChannel is the default implementation

#### add_listener() → [MessageQueueListener](#eric_sse.entities.MessageQueueListener)

Add the default listener

#### broadcast(msg: [Message](#eric_sse.entities.Message))

Enqueue a message to all listeners

* **Parameters:**
  **msg**

#### deliver_next(listener_id: str) → [Message](#eric_sse.entities.Message)

Returns next message for given listener id.
Raises a NoMessagesException if queue is empty

* **Parameters:**
  **listener_id**

#### dispatch(listener_id: str, msg: [Message](#eric_sse.entities.Message))

Adds a message to listener’s queue

* **Parameters:**
  * **listener_id**
  * **msg**

#### *async* message_stream(listener: [MessageQueueListener](#eric_sse.entities.MessageQueueListener)) → AsyncIterable[dict]

In case of failure at channel resulution time, a special message with type=’_eric_channel_closed’ is sent, and
correspondant listener is stopped

* **Parameters:**
  **listener**
* **Returns:**

#### register_listener(l: [MessageQueueListener](#eric_sse.entities.MessageQueueListener))

Adds a listener to channel

* **Parameters:**
  **l**

### *class* eric_sse.entities.Message(type: str, payload: dict | list | str | int | float | None = None)

Models a message

It’s just a container of information identified by a type.
For validation purposes you can override MessageQueueListener.on_message

### *class* eric_sse.entities.MessageQueueListener

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

#### *async* is_running() → bool

Returns listener’s state: stopped vs. running

#### is_running_sync() → bool

Returns listener’s state: stopped vs. running

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Event handler. It executes whan a message is delivered to client

#### *async* start() → None

Starts listening

#### start_sync() → None

Starts listening

#### *async* stop() → None

Stops listening

#### stop_sync() → None

Stops listening

# Prefab channels and listeners

### *class* eric_sse.prefabs.DataProcessingChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

Channel that invoke a callable in a Pool of threads

#### add_threaded_listener(callback: Callable, max_workers: int) → [ThreadPoolListener](#eric_sse.prefabs.ThreadPoolListener)

Adds a threaded listener

### *class* eric_sse.prefabs.SSEChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 5)

SSE streaming channel.

See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)
Currently, ‘id’ field is not supported.

### *class* eric_sse.prefabs.ThreadPoolListener(callback: Callable, max_workers: int)

Listener intended for consurrent processing of data.

Relies on concurrent.futures.ThreadPoolExecutor.
‘_eric_channel_closed’ Message type is intended as end of stream. Is shouls be considered as a reserved Message type

#### on_message(msg: [Message](#eric_sse.entities.Message)) → None

Event handler. It executes whan a message is delivered to client

# Prefab servers

### *class* eric_sse.servers.ChannelContainer

Helper class for managment of multiple SSE channels cases of use.

### *class* eric_sse.servers.SocketServer(file_descriptor_path: str)

An implementation of a socket server that reveives and broadcasts automatically all messages that receives

A static shortcut for starting a basic server is provided. See examples.

#### *static* start(file_descriptor_path: str)

Shortcut to start a server

# Exceptions

### *exception* eric_sse.exception.InvalidChannelException

### *exception* eric_sse.exception.InvalidListenerException

### *exception* eric_sse.exception.InvalidMessageFormat

### *exception* eric_sse.exception.NoMessagesException

Raised when trying to fetch from an empty queue
