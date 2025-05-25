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

#### \_\_init_\_(message_id, message, sender_id=None)

* **Parameters:**
  * **message_id** (*str*)
  * **message** ([*MessageContract*](#eric_sse.message.MessageContract))
  * **sender_id** (*str* *|* *None*)
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

<a id="channels-and-listeners"></a>

# Channels and listeners

<a id="eric_sse.entities.MessageQueueListener"></a>

### *class* MessageQueueListener

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

<a id="eric_sse.entities.MessageQueueListener.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.entities.MessageQueueListener.start"></a>

#### *async* start()

* **Return type:**
  None

<a id="eric_sse.entities.MessageQueueListener.start_sync"></a>

#### start_sync()

* **Return type:**
  None

<a id="eric_sse.entities.MessageQueueListener.is_running"></a>

#### *async* is_running()

* **Return type:**
  bool

<a id="eric_sse.entities.MessageQueueListener.is_running_sync"></a>

#### is_running_sync()

* **Return type:**
  bool

<a id="eric_sse.entities.MessageQueueListener.stop"></a>

#### *async* stop()

* **Return type:**
  None

<a id="eric_sse.entities.MessageQueueListener.stop_sync"></a>

#### stop_sync()

* **Return type:**
  None

<a id="eric_sse.entities.MessageQueueListener.on_message"></a>

#### on_message(msg)

Event handler. It executes when a message is delivered to client

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel

Base class for channels.

Provides functionalities for listeners and message delivery management.

[`eric_sse.queue.InMemoryMessageQueueFactory`](#eric_sse.queue.InMemoryMessageQueueFactory) is the default implementation used for queues_factory
see [`eric_sse.prefabs.SSEChannel`](#eric_sse.prefabs.SSEChannel)

* **Parameters:**
  * **stream_delay_seconds** (*int*) – Wait time in seconds between message delivery.
  * **queues_factory** ([*eric_sse.queue.AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory))

<a id="eric_sse.entities.AbstractChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, queues_factory=None)

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **queues_factory** ([*AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory) *|* *None*)

<a id="eric_sse.entities.AbstractChannel.add_listener"></a>

#### add_listener()

Add the default listener

* **Return type:**
  [*MessageQueueListener*](#eric_sse.entities.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(l)

Adds a listener to channel

* **Parameters:**
  **l** ([*MessageQueueListener*](#eric_sse.entities.MessageQueueListener))

<a id="eric_sse.entities.AbstractChannel.remove_listener"></a>

#### remove_listener(l_id)

* **Parameters:**
  **l_id** (*str*)

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

<a id="eric_sse.entities.AbstractChannel.get_listener"></a>

#### get_listener(listener_id)

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*MessageQueueListener*](#eric_sse.entities.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg)

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  *Any*

<a id="eric_sse.entities.AbstractChannel.message_stream"></a>

#### *async* message_stream(listener)

Entry point for message streaming

A message with type = ‘error’ is yeld on invalid listener or channel

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.entities.MessageQueueListener))
* **Return type:**
  *AsyncIterable*[*Any*]

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch()

* **Return type:**
  *AsyncIterable*[*Any*]

<a id="eric_sse.entities.AbstractChannel.notify_end"></a>

#### notify_end()

Broadcasts a MESSAGE_TYPE_CLOSED Message

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

SSE streaming channel.
See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Currently, ‘id’ field is not supported.

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **retry_timeout_milliseconds** (*int*)
  * **queues_factory** ([*eric_sse.queue.AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory))

<a id="eric_sse.prefabs.SSEChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, retry_timeout_milliseconds=5, queues_factory=None)

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **retry_timeout_milliseconds** (*int*)
  * **queues_factory** ([*AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory) *|* *None*)

<a id="eric_sse.prefabs.SSEChannel.payload_adapter"></a>

#### payload_adapter *: Callable[[dict | list | str | int | float | None], dict | list | str | int | float | None]*

Message payload adapter, defaults to identity (leave as is). It can be used, for example, when working in a 
context where receiver is responsible for payload deserialization, e.g. Sockets

<a id="eric_sse.prefabs.SSEChannel.adapt"></a>

#### adapt(msg)

SSE adapter.

Returns:

```default
{
    "event": "message type",
    "retry": "channel time out",
    "data": "original payload (by default)"
}
```

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  dict

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* DataProcessingChannel

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel)

Channel intended for concurrent processing of data.

Relies on [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor).
Just override **adapt** method to control output returned to clients

MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

<a id="eric_sse.prefabs.DataProcessingChannel.__init__"></a>

#### \_\_init_\_(max_workers, stream_delay_seconds=0)

* **Parameters:**
  * **max_workers** (*int*) – Num of workers to use
  * **stream_delay_seconds** (*int*) – Can be used to limit response rate of streaming. Only applies to message_stream calls.

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(l)

Launches the processing of the given listener’s queue

* **Parameters:**
  **l** ([*MessageQueueListener*](#eric_sse.entities.MessageQueueListener))
* **Return type:**
  *AsyncIterable*[dict]

<a id="eric_sse.prefabs.DataProcessingChannel.adapt"></a>

#### adapt(msg)

* **Parameters:**
  **msg** ([*Message*](#eric_sse.message.Message))
* **Return type:**
  dict

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener

Bases: [`MessageQueueListener`](#eric_sse.entities.MessageQueueListener)

Listener for distributed applications

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.__init__"></a>

#### \_\_init_\_(channel)

* **Parameters:**
  **channel** ([*AbstractChannel*](#eric_sse.entities.AbstractChannel))

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.set_action"></a>

#### set_action(name, action)

Hooks a callable to a string key.

Callables are selected when listener processes the message depending on its type.

They should return a list of Messages corresponding to response to action requested.

Reserved actions are ‘start’, ‘stop’, ‘remove’.
Receiving a message with one of these types will fire correspondant action.

* **Parameters:**
  * **name** (*str*)
  * **action** (*Callable* *[* *[*[*MessageContract*](#eric_sse.message.MessageContract) *]* *,* *list* *[*[*MessageContract*](#eric_sse.message.MessageContract) *]* *]*)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.dispatch_to"></a>

#### dispatch_to(receiver, msg)

* **Parameters:**
  * **receiver** ([*MessageQueueListener*](#eric_sse.entities.MessageQueueListener))
  * **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_message"></a>

#### on_message(msg)

Executes action correspondant to message’s type

* **Parameters:**
  **msg** ([*SignedMessage*](#eric_sse.message.SignedMessage))
* **Return type:**
  None

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.remove_sync"></a>

#### remove_sync()

Stop and unregister

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers-and-clients"></a>

# Prefab servers and clients

<a id="eric_sse.servers.SSEChannelContainer"></a>

### *class* SSEChannelContainer

Helper class for management of multiple SSE channels cases of use.

<a id="eric_sse.servers.SSEChannelContainer.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.servers.SSEChannelContainer.add"></a>

#### add(queues_factory=None)

* **Parameters:**
  **queues_factory** ([*AbstractMessageQueueFactory*](#eric_sse.queue.AbstractMessageQueueFactory) *|* *None*)
* **Return type:**
  [*SSEChannel*](#eric_sse.prefabs.SSEChannel)

<a id="eric_sse.servers.SSEChannelContainer.get"></a>

#### get(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  [*SSEChannel*](#eric_sse.prefabs.SSEChannel)

<a id="eric_sse.servers.SSEChannelContainer.rm"></a>

#### rm(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="eric_sse.servers.SSEChannelContainer.get_all_ids"></a>

#### get_all_ids()

* **Return type:**
  *Iterable*[str]

<a id="eric_sse.servers.SocketServer"></a>

### *class* SocketServer

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

<a id="eric_sse.servers.SocketServer.__init__"></a>

#### \_\_init_\_(file_descriptor_path)

* **Parameters:**
  **file_descriptor_path** (*str*)

<a id="eric_sse.servers.SocketServer.connect_callback"></a>

#### *async static* connect_callback(reader, writer)

* **Parameters:**
  * **reader** (*StreamReader*)
  * **writer** (*StreamWriter*)

<a id="eric_sse.servers.SocketServer.handle_command"></a>

#### *static* handle_command(raw_command)

* **Parameters:**
  **raw_command** (*str*)
* **Return type:**
  *AsyncIterable*[str]

<a id="eric_sse.servers.SocketServer.shutdown"></a>

#### *async* shutdown()

Graceful Shutdown

<a id="eric_sse.servers.SocketServer.main"></a>

#### *async* main()

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path)

Shortcut to start a server

* **Parameters:**
  **file_descriptor_path** (*str*)

<a id="module-eric_sse.clients"></a>

<a id="eric_sse.clients.SocketClient"></a>

### *class* SocketClient

A little facade to interact with SocketServer

<a id="eric_sse.clients.SocketClient.__init__"></a>

#### \_\_init_\_(file_descriptor_path)

* **Parameters:**
  **file_descriptor_path** (*str*)

<a id="eric_sse.clients.SocketClient.send_payload"></a>

#### *async* send_payload(payload)

Send an arbitrary payload to a socket

see [`eric_sse.servers.SocketServer`](#eric_sse.servers.SocketServer)

* **Parameters:**
  **payload** (*dict*)

<a id="eric_sse.clients.SocketClient.create_channel"></a>

#### *async* create_channel()

* **Return type:**
  str

<a id="eric_sse.clients.SocketClient.register"></a>

#### *async* register(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="eric_sse.clients.SocketClient.stream"></a>

#### *async* stream(channel_id, listener_id)

* **Return type:**
  *AsyncIterable*[str]

<a id="eric_sse.clients.SocketClient.broadcast_message"></a>

#### *async* broadcast_message(channel_id, message_type, payload)

* **Parameters:**
  * **channel_id** (*str*)
  * **message_type** (*str*)
  * **payload** (*str* *|* *dict* *|* *int* *|* *float*)

<a id="eric_sse.clients.SocketClient.dispatch"></a>

#### *async* dispatch(channel_id, receiver_id, message_type, payload)

* **Parameters:**
  * **channel_id** (*str*)
  * **receiver_id** (*str*)
  * **message_type** (*str*)
  * **payload** (*str* *|* *dict* *|* *int* *|* *float*)

<a id="eric_sse.clients.SocketClient.remove_listener"></a>

#### *async* remove_listener(channel_id, listener_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **listener_id** (*str*)

<a id="eric_sse.clients.SocketClient.remove_channel"></a>

#### *async* remove_channel(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="module-eric_sse.queue"></a>

<a id="queues"></a>

# Queues

<a id="eric_sse.queue.Queue"></a>

### *class* Queue

Bases: `ABC`

Abstract base class for queues (FIFO)

<a id="eric_sse.queue.Queue.pop"></a>

#### *abstract* pop()

Next message from the queue.

Raises a [`eric_sse.exception.NoMessagesException`](#eric_sse.exception.NoMessagesException) if the queue is empty.

* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.queue.Queue.push"></a>

#### *abstract* push(message)

* **Parameters:**
  **message** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.queue.Queue.delete"></a>

#### *abstract* delete()

Removes all messages from the queue.

* **Return type:**
  None

<a id="eric_sse.queue.AbstractMessageQueueFactory"></a>

### *class* AbstractMessageQueueFactory

Bases: `ABC`

Abstraction for queues creation

see [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.queue.AbstractMessageQueueFactory.create"></a>

#### *abstract* create()

* **Return type:**
  [*Queue*](#eric_sse.queue.Queue)

<a id="eric_sse.queue.InMemoryMessageQueueFactory"></a>

### *class* InMemoryMessageQueueFactory

Bases: [`AbstractMessageQueueFactory`](#eric_sse.queue.AbstractMessageQueueFactory)

Default implementation used by [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.queue.InMemoryMessageQueueFactory.create"></a>

#### create()

* **Return type:**
  [*Queue*](#eric_sse.queue.Queue)

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
