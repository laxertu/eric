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
For validation purposes you can override [`eric_sse.listener.MessageQueueListener.on_message`](#eric_sse.listener.MessageQueueListener.on_message)

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

<a id="module-eric_sse.connection"></a>

<a id="eric_sse.connection.Connection"></a>

### *class* Connection

Bases: `object`

A connection is just a listener and its related message queue

* **Parameters:**
  * **listener** ([*eric_sse.listener.MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*eric_sse.queues.Queue*](#eric_sse.queues.Queue))

<a id="eric_sse.connection.Connection.__init__"></a>

#### \_\_init_\_(listener, queue)

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*Queue*](#eric_sse.queues.Queue))
* **Return type:**
  None

<a id="module-eric_sse.entities"></a>

<a id="channels-and-listeners"></a>

# Channels and listeners

<a id="eric_sse.entities.AbstractChannel"></a>

### *class* AbstractChannel

Base class for channels.

Provides functionalities for listeners and message delivery management. Channel needs to be started by calling to **open()** method.

[`eric_sse.persistence.InMemoryConnectionRepository`](#eric_sse.persistence.InMemoryConnectionRepository) is the default implementation used for queues_factory
see [`eric_sse.prefabs.SSEChannel`](#eric_sse.prefabs.SSEChannel)

* **Parameters:**
  * **stream_delay_seconds** (*int*) – Wait time in seconds between message delivery.
  * **connections_repository** ([*eric_sse.persistence.ConnectionRepositoryInterface*](#eric_sse.persistence.ConnectionRepositoryInterface))

<a id="eric_sse.entities.AbstractChannel.__init__"></a>

#### \_\_init_\_(channel_id=None, stream_delay_seconds=0, connections_repository=None)

* **Parameters:**
  * **channel_id** (*str* *|* *None*)
  * **stream_delay_seconds** (*int*)
  * **connections_repository** ([*ConnectionRepositoryInterface*](#eric_sse.persistence.ConnectionRepositoryInterface) *|* *None*)

<a id="eric_sse.entities.AbstractChannel.id"></a>

#### *property* id *: str*

<a id="eric_sse.entities.AbstractChannel.open"></a>

#### open()

Starts service

<a id="eric_sse.entities.AbstractChannel.adapt"></a>

#### *abstract* adapt(msg)

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

Add the default listener and creates corresponding queue

* **Return type:**
  [*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.register_listener"></a>

#### register_listener(listener)

Registers listener and creates corresponding queue

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))

<a id="eric_sse.entities.AbstractChannel.register_connection"></a>

#### register_connection(listener, queue)

Registers a Connection with listener and queue

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **queue** ([*Queue*](#eric_sse.queues.Queue))

<a id="eric_sse.entities.AbstractChannel.remove_listener"></a>

#### remove_listener(listener_id)

* **Parameters:**
  **listener_id** (*str*)

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
  [*MessageQueueListener*](#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.entities.AbstractChannel.watch"></a>

#### *async* watch()

* **Return type:**
  *AsyncIterable*[*Any*]

<a id="eric_sse.entities.AbstractChannel.get_listeners_ids"></a>

#### get_listeners_ids()

* **Return type:**
  list[str]

<a id="module-eric_sse.listener"></a>

<a id="eric_sse.listener.MessageQueueListener"></a>

### *class* MessageQueueListener

Base class for listeners.

Optionally you can override on_message method if you need to inject code at message delivery time.

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

<a id="persistence"></a>

# Persistence

**Channels**

![image](_static/persistence-layer-channels.png)

**Connections**

![image](_static/persistence-layer-connections.png)

<a id="module-eric_sse.persistence"></a>

This module is intended to those who want to create their own persistence layer.

**Writing a custom persistence layer**

you need to implement the following interfaces:

* [`eric_sse.persistence.PersistableQueue`](#eric_sse.persistence.PersistableQueue)
* [`eric_sse.persistence.ConnectionRepositoryInterface`](#eric_sse.persistence.ConnectionRepositoryInterface)
* [`eric_sse.persistence.ChannelRepositoryInterface`](#eric_sse.persistence.ChannelRepositoryInterface)
* A **Redis** concrete implementation of interfaces is available at [https://pypi.org/project/eric-redis-queues/](https://pypi.org/project/eric-redis-queues/)

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin"></a>

### *class* ObjectAsKeyValuePersistenceMixin

Bases: `ABC`

Adds KV persistence support.

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_key"></a>

#### *abstract property* kv_key *: str*

The key to use when persisting object

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_value_as_dict"></a>

#### *abstract property* kv_value_as_dict *: dict*

Returns value that will be persisted as a dictionary.

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.setup_by_dict"></a>

#### *abstract* setup_by_dict(setup)

Does de necessary setup of object given its persisted values

* **Parameters:**
  **setup** (*dict*)

<a id="eric_sse.persistence.PersistableQueue"></a>

### *class* PersistableQueue

Bases: [`Queue`](#eric_sse.queues.Queue), [`ObjectAsKeyValuePersistenceMixin`](#eric_sse.persistence.ObjectAsKeyValuePersistenceMixin), `ABC`

Concrete implementations of methods should perform in **Queues** ones their I/O operations, and define in **ObjectAsKeyValuePersistenceMixin** ones their correspondant persistence strategy

<a id="eric_sse.persistence.ObjectRepositoryInterface"></a>

### *class* ObjectRepositoryInterface

Bases: `ABC`

<a id="eric_sse.persistence.ObjectRepositoryInterface.load"></a>

#### *abstract* load()

Returns an Iterable of all persisted objects of correspondant concrete implementation.

* **Return type:**
  *Iterable*[[*ObjectAsKeyValuePersistenceMixin*](#eric_sse.persistence.ObjectAsKeyValuePersistenceMixin)]

<a id="eric_sse.persistence.ObjectRepositoryInterface.persist"></a>

#### *abstract* persist(persistable)

* **Parameters:**
  **persistable** ([*ObjectAsKeyValuePersistenceMixin*](#eric_sse.persistence.ObjectAsKeyValuePersistenceMixin))

<a id="eric_sse.persistence.ObjectRepositoryInterface.delete"></a>

#### *abstract* delete(key)

* **Parameters:**
  **key** (*str*)

<a id="eric_sse.persistence.ChannelRepositoryInterface"></a>

### *class* ChannelRepositoryInterface

Bases: [`ObjectRepositoryInterface`](#eric_sse.persistence.ObjectRepositoryInterface)

<a id="eric_sse.persistence.ChannelRepositoryInterface.delete_listener"></a>

#### *abstract* delete_listener(channel_id, listener_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **listener_id** (*str*)
* **Return type:**
  None

<a id="eric_sse.persistence.ConnectionRepositoryInterface"></a>

### *class* ConnectionRepositoryInterface

Bases: `ABC`

Abstraction for connections creation.

It exposes methods to be used by ChannelRepositoryInterface implementations for connections loading.

see [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.persistence.ConnectionRepositoryInterface.create_queue"></a>

#### *abstract* create_queue(listener_id)

Returns a concrete Queue instance.

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*Queue*](#eric_sse.queues.Queue)

<a id="eric_sse.persistence.ConnectionRepositoryInterface.persist"></a>

#### *abstract* persist(channel_id, connection)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.persistence.ConnectionRepositoryInterface.load_all"></a>

#### *abstract* load_all()

Returns an Iterable of all persisted connections

* **Return type:**
  *Iterable*[[*Connection*](#eric_sse.connection.Connection)]

<a id="eric_sse.persistence.ConnectionRepositoryInterface.load"></a>

#### *abstract* load(channel_id)

Returns an Iterable of all persisted connections of a given channel

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](#eric_sse.connection.Connection)]

<a id="eric_sse.persistence.ConnectionRepositoryInterface.delete"></a>

#### *abstract* delete(channel_id, listener_id)

Removes a persisted [`eric_sse.connection.Connection`](#eric_sse.connection.Connection) given its correspondant listener id

* **Parameters:**
  * **channel_id** (*str*)
  * **listener_id** (*str*)
* **Return type:**
  None

<a id="eric_sse.persistence.InMemoryConnectionRepository"></a>

### *class* InMemoryConnectionRepository

Bases: [`ConnectionRepositoryInterface`](#eric_sse.persistence.ConnectionRepositoryInterface)

Default implementation used by [`eric_sse.entities.AbstractChannel`](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.persistence.InMemoryConnectionRepository.create_queue"></a>

#### create_queue(listener_id)

Returns a concrete Queue instance.

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*Queue*](#eric_sse.queues.Queue)

<a id="eric_sse.persistence.InMemoryConnectionRepository.persist"></a>

#### persist(channel_id, connection)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection** ([*Connection*](#eric_sse.connection.Connection))
* **Return type:**
  None

<a id="eric_sse.persistence.InMemoryConnectionRepository.load_all"></a>

#### load_all()

Returns an Iterable of all persisted connections

* **Return type:**
  *Iterable*[[*Connection*](#eric_sse.connection.Connection)]

<a id="eric_sse.persistence.InMemoryConnectionRepository.load"></a>

#### load(channel_id)

Returns an Iterable of all persisted connections of a given channel

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](#eric_sse.connection.Connection)]

<a id="eric_sse.persistence.InMemoryConnectionRepository.delete"></a>

#### delete(channel_id, listener_id)

Removes a persisted [`eric_sse.connection.Connection`](#eric_sse.connection.Connection) given its correspondant listener id

* **Parameters:**
  * **channel_id** (*str*)
  * **listener_id** (*str*)
* **Return type:**
  None

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel

Bases: [`AbstractChannel`](#eric_sse.entities.AbstractChannel), [`ObjectAsKeyValuePersistenceMixin`](#eric_sse.persistence.ObjectAsKeyValuePersistenceMixin)

SSE streaming channel.
See [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Currently, ‘id’ field is not supported.

* **Parameters:**
  * **stream_delay_seconds** (*int*)
  * **retry_timeout_milliseconds** (*int*)
  * **connections_repository** ([*eric_sse.persistence.ConnectionRepositoryInterface*](#eric_sse.persistence.ConnectionRepositoryInterface))

<a id="eric_sse.prefabs.SSEChannel.__init__"></a>

#### \_\_init_\_(channel_id=None, stream_delay_seconds=0, retry_timeout_milliseconds=5, connections_repository=None)

* **Parameters:**
  * **channel_id** (*str* *|* *None*)
  * **stream_delay_seconds** (*int*)
  * **retry_timeout_milliseconds** (*int*)
  * **connections_repository** ([*ConnectionRepositoryInterface*](#eric_sse.persistence.ConnectionRepositoryInterface) *|* *None*)

<a id="eric_sse.prefabs.SSEChannel.payload_adapter"></a>

#### payload_adapter *: Callable[[dict | list | str | int | float | None], dict | list | str | int | float | None]*

Message payload adapter, defaults to identity (leave as is). It can be used, for example, when working in a 
context where receiver is responsible for payload deserialization, e.g. Sockets

<a id="eric_sse.prefabs.SSEChannel.kv_key"></a>

#### *property* kv_key *: str*

The key to use when persisting object

<a id="eric_sse.prefabs.SSEChannel.kv_value_as_dict"></a>

#### *property* kv_value_as_dict *: dict*

Returns value that will be persisted as a dictionary.

<a id="eric_sse.prefabs.SSEChannel.setup_by_dict"></a>

#### setup_by_dict(setup)

Does de necessary setup of object given its persisted values

* **Parameters:**
  **setup** (*dict*)

<a id="eric_sse.prefabs.SSEChannel.create_from_dict"></a>

#### *static* create_from_dict(params, connection_repository)

* **Parameters:**
  * **params** (*dict*)
  * **connection_repository** ([*ConnectionRepositoryInterface*](#eric_sse.persistence.ConnectionRepositoryInterface))
* **Return type:**
  [*AbstractChannel*](#eric_sse.entities.AbstractChannel)

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

Relies on [concurrent.futures.Executor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor).
Just override **adapt** method to control output returned to clients

MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

<a id="eric_sse.prefabs.DataProcessingChannel.__init__"></a>

#### \_\_init_\_(max_workers, stream_delay_seconds=0, executor_class=<class 'concurrent.futures.thread.ThreadPoolExecutor'>)

* **Parameters:**
  * **max_workers** (*int*) – Num of workers to use
  * **stream_delay_seconds** (*int*) – Can be used to limit response rate of streaming. Only applies to message_stream calls.
  * **executor_class** (*type*) – The constructor of some Executor class. Defaults to  [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor).

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(listener)

Performs queue processing of a given listener, returns an AsyncIterable of dictionaries containing message process result. See **adapt** method

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  *AsyncIterable*[dict]

<a id="eric_sse.prefabs.DataProcessingChannel.adapt"></a>

#### adapt(msg)

Returns a dictionary in the following format:

```default
{
    "event": message type
    "data": message payload
}
```

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  dict

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener

Bases: [`MessageQueueListener`](#eric_sse.listener.MessageQueueListener)

Listener for distributed applications

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.set_action"></a>

#### set_action(name, action)

Hooks a callable to a string key.

Callables are selected when listener processes the message depending on its type.

They should return a list of MessageContract instances corresponding to response to action requested.

Reserved actions are ‘start’, ‘stop’.
Receiving a message with one of these types will fire corresponding action.

* **Parameters:**
  * **name** (*str*)
  * **action** (*Callable* *[* *[*[*MessageContract*](#eric_sse.message.MessageContract) *]* *,* *list* *[*[*MessageContract*](#eric_sse.message.MessageContract) *]* *]*)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.dispatch_to"></a>

#### dispatch_to(receiver, msg)

* **Parameters:**
  * **receiver** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **msg** ([*MessageContract*](#eric_sse.message.MessageContract))

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_message"></a>

#### on_message(msg)

Executes action corresponding to message’s type

* **Parameters:**
  **msg** ([*SignedMessage*](#eric_sse.message.SignedMessage))
* **Return type:**
  None

<a id="eric_sse.prefabs.SimpleDistributedApplicationChannel"></a>

### *class* SimpleDistributedApplicationChannel

Bases: [`SSEChannel`](#eric_sse.prefabs.SSEChannel)

<a id="eric_sse.prefabs.SimpleDistributedApplicationChannel.register_listener"></a>

#### register_listener(listener)

Registers listener and creates corresponding queue

* **Parameters:**
  **listener** ([*SimpleDistributedApplicationListener*](#eric_sse.prefabs.SimpleDistributedApplicationListener))

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers-and-clients"></a>

# Prefab servers and clients

<a id="eric_sse.servers.ChannelContainer"></a>

### *class* ChannelContainer

Helper class for management of multiple channels cases of use.

<a id="eric_sse.servers.ChannelContainer.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.servers.ChannelContainer.register"></a>

#### register(channel)

* **Parameters:**
  **channel** ([*AbstractChannel*](#eric_sse.entities.AbstractChannel))
* **Return type:**
  None

<a id="eric_sse.servers.ChannelContainer.get"></a>

#### get(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  [*AbstractChannel*](#eric_sse.entities.AbstractChannel)

<a id="eric_sse.servers.ChannelContainer.rm"></a>

#### rm(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="eric_sse.servers.ChannelContainer.get_all_ids"></a>

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
  **file_descriptor_path** (*str*) – See **start** method

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path)

Shortcut to start a server given a file descriptor path

* **Parameters:**
  **file_descriptor_path** (*str*) – file descriptor path, all understood by [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) is fine

<a id="eric_sse.servers.SocketServer.shutdown"></a>

#### *async* shutdown()

Graceful Shutdown

<a id="eric_sse.servers.SocketServer.main"></a>

#### *async* main()

Starts the server

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

Raises a [`eric_sse.exception.NoMessagesException`](#eric_sse.exception.NoMessagesException) if the queue is empty.

* **Return type:**
  [*MessageContract*](#eric_sse.message.MessageContract)

<a id="eric_sse.queues.Queue.push"></a>

#### *abstract* push(message)

* **Parameters:**
  **message** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  None

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

<a id="eric_sse.exception.RepositoryError"></a>

### *exception* RepositoryError

Raised when an unexpected error occurs while trying to fetch messages from a queue.

Concrete implementations of `Queue` should wrap here the unexpected exceptions they catch before raising, and
an [`eric_sse.exception.NoMessagesException`](#eric_sse.exception.NoMessagesException) when a pop is requested on an empty queue.

<a id="module-eric_sse.profile"></a>

<a id="profiling-tools"></a>

# Profiling tools

<a id="eric_sse.profile.ListenerWrapper"></a>

### *class* ListenerWrapper

Bases: [`MessageQueueListener`](#eric_sse.listener.MessageQueueListener)

Wraps a listener to profile its on_message method.

<a id="eric_sse.profile.ListenerWrapper.__init__"></a>

#### \_\_init_\_(listener, profile_messages=False)

* **Parameters:**
  * **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
  * **profile_messages** (*bool*)

<a id="eric_sse.profile.ListenerWrapper.on_message"></a>

#### on_message(msg)

Performs on_message profiling

* **Parameters:**
  **msg** ([*MessageContract*](#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.profile.DataProcessingChannelProfiler"></a>

### *class* DataProcessingChannelProfiler

Bases: `object`

<a id="eric_sse.profile.DataProcessingChannelProfiler.__init__"></a>

#### \_\_init_\_(channel)

Wraps a channel to profile its process_queue method.

* **Parameters:**
  **channel** ([*DataProcessingChannel*](#eric_sse.prefabs.DataProcessingChannel))

<a id="eric_sse.profile.DataProcessingChannelProfiler.add_listener"></a>

#### add_listener(listener)

Adds a listener to the channel after having wrapped it

* **Parameters:**
  **listener** ([*MessageQueueListener*](#eric_sse.listener.MessageQueueListener))
* **Return type:**
  [*ListenerWrapper*](#eric_sse.profile.ListenerWrapper)

<a id="eric_sse.profile.DataProcessingChannelProfiler.run"></a>

#### *async* run(listener)

Runs profile

* **Parameters:**
  **listener** ([*ListenerWrapper*](#eric_sse.profile.ListenerWrapper))
