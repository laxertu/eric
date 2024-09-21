# The lightweight library for async messaging nobody expects. 

Features

* Send to listener and broadcast
* SSE format was adopted by design, is order to make library suitable for such kind of model
* Socket support
* Listeners with "on message" callback support

Possible applications

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)

Trivia

Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric

## Core Entities
Models a message
<a name="eric.entities.Message"></a>
### *class* eric.entities.Message(type: str, payload: dict | list | str | int | float | None = None)

It’s just a container of information identified by a type.
For validation purposes you can override MessageQueueListener.on_message


### *class* eric.entities.AbstractChannel

Base class for channels.

Provides functionalities for listeners and message delivery management.
SSEChannel is the default implementation

#### add_listener() → [MessageQueueListener](#eric.entities.MessageQueueListener)

Adds a the default listener to channel

* **Parameters:**
  **l_class** – a valid MessageQueueListener class constructor.

#### broadcast(msg: [Message](#eric.entities.Message))

Enqueue a message to all listeners

* **Parameters:**
  **msg**

#### deliver_next(listener_id: str) → [Message](#eric.entities.Message)

Returns next message for given listener id.
Raises a NoMessagesException if queue is empty

* **Parameters:**
  **listener_id**

#### dispatch(listener_id: str, msg: [Message](#eric.entities.Message))

Adds a message to listener’s queue

* **Parameters:**
  * **listener_id**
  * **msg**

#### *abstract async* message_stream(listener: [MessageQueueListener](#eric.entities.MessageQueueListener)) → AsyncIterable[Any]

Entry point for message streaming

#### register_listener(l: [MessageQueueListener](#eric.entities.MessageQueueListener))

Adds a listener to channel

* **Parameters:**
  **l**

### *class* eric.entities.Message(type: str, payload: dict | list | str | int | float | None = None)

Models a message

It’s just a container of information identified by a type.
For validation purposes you can override MessageQueueListener.on_message

### *class* <a name="eric.entities.MessageQueueListener">eric.entities.MessageQueueListener</a>

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

#### *async* is_running() → bool

Returns listener’s state: stopped vs. running

#### is_running_sync() → bool

Returns listener’s state: stopped vs. running

#### on_message(msg: [Message](#eric.entities.Message)) → None

Event handler. It executes whan a message is delivered to client

#### *async* start() → None

Starts listening

#### start_sync() → None

Starts listening

#### *async* stop() → None

Stops listening

#### *async* stop_sync() → None

Stops listening

### *class* eric.entities.SSEChannel(stream_delay_seconds: int = 0, retry_timeout_millisedonds: int = 15000)

SSE streaming channel.

See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)
Currently, ‘id’ field is not supported.

#### *async* message_stream(listener: [MessageQueueListener](#eric.entities.MessageQueueListener)) → AsyncIterable[dict]

In case of failure at channel resulution time, a special message with type=’_eric_channel_closed’ is sent, and
correspondant listener is stopped

* **Parameters:**
  **listener**
* **Returns:**

## Prefab servers

### *class* eric.servers.ChannelContainer

Helper class for managment of multiple SSE channels cases of use.

### *class* eric.servers.SocketServer(file_descriptor_path: str)

An implementation of a socket server that reveives and broadcasts automatically all messages that receives

A static shortcut for starting a basic server is provided. See examples.

#### *static* start(file_descriptor_path: str)

Shortcut to start a server

## Exceptions

### *exception* eric.exception.InvalidChannelException

### *exception* eric.exception.InvalidListenerException

### *exception* eric.exception.InvalidMessageFormat

### *exception* eric.exception.NoMessagesException

Raised when trying to fetch from an empty queue
