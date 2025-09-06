<a id="prefabs"></a>

# Prefabs

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

# Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel

Bases: [`AbstractChannel`](entities.md#eric_sse.entities.AbstractChannel)

SSE streaming channel.
See [Mozilla docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Currently, ‘id’ field is not supported.

<a id="eric_sse.prefabs.SSEChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, retry_timeout_milliseconds=5, channel_id=None, connections_factory=None)

* **Parameters:**
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/library/functions.html#int))
  * **retry_timeout_milliseconds** ([*int*](https://docs.python.org/3/library/functions.html#int))
  * **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*)
  * **connections_factory** ([*ConnectionsFactory*](entities.md#eric_sse.connection.ConnectionsFactory) *|* *None*)

<a id="eric_sse.prefabs.SSEChannel.adapt"></a>

#### adapt(msg)

SSE adapter.

Returns:

```default
{
    "event": "message type",
    "retry": "channel time out",
    "data": "original payload"
}
```

* **Parameters:**
  **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* DataProcessingChannel

Bases: [`AbstractChannel`](entities.md#eric_sse.entities.AbstractChannel)

Channel intended for concurrent processing of data.

Relies on [concurrent.futures.Executor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor).
Just override **adapt** method to control output returned to clients

<a id="eric_sse.prefabs.DataProcessingChannel.__init__"></a>

#### \_\_init_\_(max_workers, stream_delay_seconds=0, executor_class=<class 'concurrent.futures.thread.ThreadPoolExecutor'>)

* **Parameters:**
  * **max_workers** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Num of workers to use
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Can be used to limit response rate of streaming. Only applies to message_stream calls.
  * **executor_class** ([*type*](https://docs.python.org/3/library/functions.html#type)) – The constructor of some Executor class. Defaults to  [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor).

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(listener)

Performs queue processing of a given listener, returns an AsyncIterable of dictionaries containing message process result. See **adapt** method

* **Parameters:**
  **listener** ([*MessageQueueListener*](entities.md#eric_sse.listener.MessageQueueListener))
* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[dict](https://docs.python.org/3/library/stdtypes.html#dict)]

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
  **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener

Bases: [`MessageQueueListener`](entities.md#eric_sse.listener.MessageQueueListener)

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
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **action** ([*Callable*](https://docs.python.org/3/library/typing.html#typing.Callable) *[* *[*[*MessageContract*](entities.md#eric_sse.message.MessageContract) *]* *,* [*list*](https://docs.python.org/3/library/stdtypes.html#list) *[*[*MessageContract*](entities.md#eric_sse.message.MessageContract) *]* *]*)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.dispatch_to"></a>

#### dispatch_to(receiver, msg)

* **Parameters:**
  * **receiver** ([*MessageQueueListener*](entities.md#eric_sse.listener.MessageQueueListener))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_message"></a>

#### on_message(msg)

Executes action corresponding to message’s type

* **Parameters:**
  **msg** ([*SignedMessage*](entities.md#eric_sse.message.SignedMessage))
* **Return type:**
  None

<a id="eric_sse.prefabs.SimpleDistributedApplicationChannel"></a>

### *class* SimpleDistributedApplicationChannel

Bases: [`SSEChannel`](#eric_sse.prefabs.SSEChannel)

<a id="eric_sse.prefabs.SimpleDistributedApplicationChannel.register_listener"></a>

#### register_listener(listener)

Registers an existing listener

* **Parameters:**
  **listener** ([*SimpleDistributedApplicationListener*](#eric_sse.prefabs.SimpleDistributedApplicationListener))

<a id="eric_sse.prefabs.SSEChannelRepository"></a>

### *class* SSEChannelRepository

Bases: [`AbstractChannelRepository`](persistence.md#eric_sse.repository.AbstractChannelRepository)

Enable SSE channels persistence

<a id="eric_sse.prefabs.SSEChannelRepository.create"></a>

#### create(channel_data)

Creates a new channel and configures it depending on channel_data.

* **Parameters:**
  **channel_data** ([*dict*](https://docs.python.org/3/library/stdtypes.html#dict))
* **Return type:**
  [*SSEChannel*](#eric_sse.prefabs.SSEChannel)

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
  **channel** ([*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel))
* **Return type:**
  None

<a id="eric_sse.servers.ChannelContainer.register_iterable"></a>

#### register_iterable(channels)

* **Parameters:**
  **channels** ([*Iterable*](https://docs.python.org/3/library/typing.html#typing.Iterable) *[*[*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel) *]*)
* **Return type:**
  None

<a id="eric_sse.servers.ChannelContainer.get"></a>

#### get(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
* **Return type:**
  [*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel)

<a id="eric_sse.servers.ChannelContainer.rm"></a>

#### rm(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))

<a id="eric_sse.servers.ChannelContainer.get_all_ids"></a>

#### get_all_ids()

* **Return type:**
  [*Iterable*](https://docs.python.org/3/library/typing.html#typing.Iterable)[[str](https://docs.python.org/3/library/stdtypes.html#str)]

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
  **file_descriptor_path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – See **start** method

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path)

Shortcut to start a server given a file descriptor path

* **Parameters:**
  **file_descriptor_path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – file descriptor path, all understood by [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) is fine

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
  **file_descriptor_path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.send_payload"></a>

#### *async* send_payload(payload)

Send an arbitrary payload to a socket

see [`SocketServer`](#eric_sse.servers.SocketServer)

* **Parameters:**
  **payload** ([*dict*](https://docs.python.org/3/library/stdtypes.html#dict))

<a id="eric_sse.clients.SocketClient.create_channel"></a>

#### *async* create_channel()

* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="eric_sse.clients.SocketClient.register"></a>

#### *async* register(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.stream"></a>

#### *async* stream(channel_id, listener_id)

* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[str](https://docs.python.org/3/library/stdtypes.html#str)]

<a id="eric_sse.clients.SocketClient.broadcast_message"></a>

#### *async* broadcast_message(channel_id, message_type, payload)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **message_type** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **payload** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*dict*](https://docs.python.org/3/library/stdtypes.html#dict) *|* [*int*](https://docs.python.org/3/library/functions.html#int) *|* [*float*](https://docs.python.org/3/library/functions.html#float))

<a id="eric_sse.clients.SocketClient.dispatch"></a>

#### *async* dispatch(channel_id, receiver_id, message_type, payload)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **receiver_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **message_type** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **payload** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*dict*](https://docs.python.org/3/library/stdtypes.html#dict) *|* [*int*](https://docs.python.org/3/library/functions.html#int) *|* [*float*](https://docs.python.org/3/library/functions.html#float))

<a id="eric_sse.clients.SocketClient.remove_listener"></a>

#### *async* remove_listener(channel_id, listener_id)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
  * **listener_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.remove_channel"></a>

#### *async* remove_channel(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))
