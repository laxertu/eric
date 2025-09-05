<a id="entities"></a>

# Entities

<a id="module-eric_sse.message"></a>

<a id="messages"></a>

# Messages

<a id="eric_sse.message.MessageContract"></a>

### *class* MessageContract

Bases: `ABC`

Contract class for messages

A message is just a container of information identified by a type.
For validation purposes you can override its [`on_message()`](#eric_sse.listener.MessageQueueListener.on_message) method.

<a id="eric_sse.message.MessageContract.type"></a>

#### *abstract property* type *: str*

Message type

<a id="eric_sse.message.MessageContract.payload"></a>

#### *abstract property* payload *: dict | list | str | int | float | None*

Message payload

<a id="eric_sse.message.Message"></a>

### *class* Message

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Models a simple message

<a id="eric_sse.message.Message.__init__"></a>

#### \_\_init_\_(msg_type, msg_payload=None)

* **Parameters:**
  * **msg_type** (*str*)
  * **msg_payload** (*dict* *|* *list* *|* *str* *|* *int* *|* *float* *|* *None*)
* **Return type:**
  None

<a id="eric_sse.message.Message.type"></a>

#### *property* type *: str*

Message type

<a id="eric_sse.message.Message.payload"></a>

#### *property* payload *: dict | list | str | int | float | None*

Message payload

<a id="eric_sse.message.UniqueMessage"></a>

### *class* UniqueMessage

Bases: [`MessageContract`](#eric_sse.message.MessageContract)

Messages plus an unique identifier

<a id="eric_sse.message.UniqueMessage.__init__"></a>

#### \_\_init_\_(message, sender_id=None, message_id=None)

* **Parameters:**
  * **message** ([*MessageContract*](#eric_sse.message.MessageContract))
  * **sender_id** (*str* *|* *None*)
  * **message_id** (*str* *|* *None*)
* **Return type:**
  None

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

#### *property* payload *: dict | list | str | int | float | None*

Message payload

<a id="eric_sse.message.SignedMessage"></a>

### *class* SignedMessage

Bases: [`Message`](#eric_sse.message.Message)

Message plus sender id

<a id="eric_sse.message.SignedMessage.__init__"></a>

#### \_\_init_\_(sender_id, msg_type, msg_payload=None)

* **Parameters:**
  * **sender_id** (*str*)
  * **msg_type** (*str*)
  * **msg_payload** (*dict* *|* *list* *|* *str* *|* *int* *|* *float* *|* *None*)

<a id="eric_sse.message.SignedMessage.sender_id"></a>

#### *property* sender_id *: str*

Returns the id of the listener that sent the message

<a id="module-eric_sse.entities"></a>

<a id="channels-and-connections"></a>

# Channels and connections

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel

Bases: `ABC`

Base class for channels.

Provides functionalities for listeners and message delivery management.

[`InMemoryConnectionsFactory`](#eric_sse.connection.InMemoryConnectionsFactory) is the default implementation used for **connections_factory** parameter.

see [`SSEChannel`](prefabs.md#eric_sse.prefabs.SSEChannel)

* **Parameters:**
  * **stream_delay_seconds** (*int*) – Wait time in seconds between message delivery.
  * **channel_id** (*str*) – Optionally sets the channel id.
  * **connections_factory** ([*ConnectionsFactory*](#eric_sse.connection.ConnectionsFactory)) – Factory to be used for creating connections instances on channel subscriptions.

<a id="eric_sse.entities.AbstractChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, channel_id=None, connections_factory=None)

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **channel_id** (*str* *|* *None*)
  * **connections_factory** ([*ConnectionsFactory*](#eric_sse.connection.ConnectionsFactory) *|* *None*)

<a id="eric_sse.entities.AbstractChannel.id"></a>

#### *property* id *: str*

Unique identifier for this channel, it can be set by **channel_id** constructor parameter

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg)

Models output of channel streams

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  *Any*

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener)

Entry point for message streaming

A message with type = ‘error’ is yield on invalid listener

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  *AsyncIterable*[*Any*]

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

Register and existing connection.

**Warning**: Listener and queue should belong to the same classes returned by connection factory to avoid compatibility issues with persistence layer

* **Parameters:**
  **connection** ([*Connection*](#eric_sse.connection.Connection))

<a id="eric_sse.entities.AbstractChannel.deliver_next"></a>

#### deliver_next(listener_id)

Returns next message for given listener id.

Raises a NoMessagesException if queue is empty

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.entities.AbstractChannel.dispatch"></a>

#### dispatch(listener_id, msg)

Adds a message to listener’s queue

* **Parameters:**
  * **listener_id** (*str*)
  * **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="eric_sse.entities.AbstractChannel.broadcast"></a>

#### broadcast(msg)

Enqueue a message to all listeners

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="module-eric_sse.connection"></a>

<a id="eric_sse.connection.Connection"></a>

### *class* Connection

Bases: `object`

A connection is just a listener and its related message queue

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*Queue*](#eric_sse.queues.Queue))

<a id="eric_sse.connection.Connection.__init__"></a>

#### \_\_init_\_(listener, queue, connection_id=None)

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*Queue*](#eric_sse.queues.Queue))
  * **connection_id** (*str* *|* *None*)

<a id="eric_sse.connection.ConnectionsFactory"></a>

### *class* ConnectionsFactory

Bases: `ABC`

<a id="eric_sse.connection.ConnectionsFactory.create"></a>

#### *abstract* create(listener=None)

Creates a connection

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)) – If provided, assigns a concrete listener
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)

<a id="eric_sse.connection.InMemoryConnectionsFactory"></a>

### *class* InMemoryConnectionsFactory

Bases: [`ConnectionsFactory`](#eric_sse.connection.ConnectionsFactory)

Creates Connections with In memory queues (no persistence support)

<a id="eric_sse.connection.InMemoryConnectionsFactory.create"></a>

#### create(listener=None)

Creates a connection

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)) – If provided, assigns a concrete listener
* **Return type:**
  [*Connection*](#eric_sse.connection.Connection)

<a id="module-eric_sse.queues"></a>

<a id="queues"></a>

# Queues

<a id="eric_sse.queues.Queue"></a>

### *class* Queue

Bases: `ABC`

Abstract base class for queues (FIFO).

<a id="eric_sse.queues.Queue.pop"></a>

#### *abstract* pop()

Next message from the queue.

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if the queue is empty.

* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.queues.Queue.push"></a>

#### *abstract* push(message)

* **Parameters:**
  **message** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="module-eric_sse.listener"></a>

<a id="listeners"></a>

# Listeners

<a id="eric_sse.listener.MessageQueueListener"></a>

### *class* MessageQueueListener

Bases: `object`

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.listener.MessageQueueListener.__init__"></a>

#### \_\_init_\_(listener_id=None)

* **Parameters:**
  **listener_id** (*str* *|* *None*)

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
  bool
