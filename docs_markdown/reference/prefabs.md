<a id="prefabs"></a>

# Prefabs

<a id="module-eric_sse.prefabs"></a>

<a id="prefab-channels-and-listeners"></a>

## Prefab channels and listeners

<a id="eric_sse.prefabs.SSEChannel"></a>

### *class* SSEChannel

Bases: [`AbstractChannel`](entities.md#eric_sse.entities.AbstractChannel)[[`MIn`](entities.md#eric_sse.message.MIn), [`MOut`](entities.md#eric_sse.message.MOut)]

SSE streaming channel.
See [Mozilla docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format)

Messages are sent as SSE events, see [`adapt()`](#eric_sse.prefabs.SSEChannel.adapt), and stream errors as events of type `error`, see
[`adapt_error()`](#eric_sse.prefabs.SSEChannel.adapt_error).

<a id="eric_sse.prefabs.SSEChannel.__init__"></a>

#### \_\_init_\_(stream_delay_seconds=0, retry_timeout_milliseconds=5, channel_id=None, connections_factory=None)

* **Parameters:**
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/builtins/functions.html#int))
  * **retry_timeout_milliseconds** ([*int*](https://docs.python.org/3/builtins/functions.html#int))
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*)
  * **connections_factory** ([*ConnectionsFactory*](entities.md#eric_sse.connection.ConnectionsFactory) *|* *None*)

<a id="eric_sse.prefabs.SSEChannel.to_dict"></a>

#### to_dict()

Channel configuration to be persisted. Keys must be constructor parameters, see `from_dict()`.

Subclasses with additional configuration should extend it:

```default
def to_dict(self) -> dict:
    return {**super().to_dict(), 'my_param': self.my_param}
```

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.SSEChannel.adapt"></a>

#### adapt(msg)

SSE adapter.

Returns:

```default
{
    "event": "message type",
    "retry": "channel time out",
    "data": "original payload",
    "id": "message id"
}
```

“id” is optional, as in SSE specs: it’s there only if the message has an [`id`](entities.md#eric_sse.message.MessageContract.id).

* **Parameters:**
  **msg** ([*MOut*](entities.md#eric_sse.message.MOut))
* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.SSEChannel.adapt_error"></a>

#### adapt_error(exception)

SSE adapter for stream errors.

Returns:

```default
{
    "event": "error",
    "retry": "channel time out",
    "data": {"error": "exception class name", "message": "exception message"}
}
```

* **Parameters:**
  **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.DataProcessingChannel"></a>

### *class* DataProcessingChannel

Bases: [`AbstractChannel`](entities.md#eric_sse.entities.AbstractChannel)[[`MIn`](entities.md#eric_sse.message.MIn), [`MOut`](entities.md#eric_sse.message.MOut)]

Channel intended for concurrent processing of data.

Relies on [concurrent.futures.Executor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor).
Just override **adapt** method to control output returned to clients

<a id="eric_sse.prefabs.DataProcessingChannel.__init__"></a>

#### \_\_init_\_(max_workers, stream_delay_seconds=0, executor_class=<class 'concurrent.futures.thread.ThreadPoolExecutor'>, channel_id=None, connections_factory=None)

* **Parameters:**
  * **max_workers** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Num of workers to use
  * **stream_delay_seconds** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Can be used to limit response rate of streaming. Only applies to message_stream calls.
  * **executor_class** ([*type*](https://docs.python.org/3/builtins/functions.html#type)) – The constructor of some Executor class. Defaults to  [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor).
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Optionally sets the channel id.
  * **connections_factory** ([*ConnectionsFactory*](entities.md#eric_sse.connection.ConnectionsFactory) *|* *None*) – See [`AbstractChannel`](entities.md#eric_sse.entities.AbstractChannel).

<a id="eric_sse.prefabs.DataProcessingChannel.to_dict"></a>

#### to_dict()

**executor_class** is stored as a class object: the storage engine must be able to serialise it.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.DataProcessingChannel.process_queue"></a>

#### *async* process_queue(connection_id)

Processes the messages in the queue of a given connection: runs its listener’s `on_message` concurrently in the executor,
and yields each message, adapted, as soon as it’s processed. See **adapt** method.

Errors are handled as by [`deliver_next()`](entities.md#eric_sse.entities.AbstractChannel.deliver_next), in the channel’s process:
listener errors are logged and passed to error handlers, and the message is yielded anyway. Queue errors and a
[`StoppedListenerException`](exceptions.md#eric_sse.exception.StoppedListenerException) are re-raised after the messages already popped are
yielded, so they are not lost.

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[dict](https://docs.python.org/3/builtins/stdtypes.html#dict)]

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
  **msg** ([*MOut*](entities.md#eric_sse.message.MOut))
* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.DataProcessingChannel.adapt_error"></a>

#### adapt_error(exception)

Returns a dictionary in the following format:

```default
{
    "event": "error",
    "data": {"error": "exception class name", "message": "exception message"}
}
```

* **Parameters:**
  **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener"></a>

### *class* SimpleDistributedApplicationListener

Bases: [`MessageQueueListener`](entities.md#eric_sse.listener.MessageQueueListener)[[`SignedMessage`](entities.md#eric_sse.message.SignedMessage)]

Listener for distributed applications.

It dispatches through the channel it is registered to, see [`on_registered()`](#eric_sse.prefabs.SimpleDistributedApplicationListener.on_registered): any channel, including
when listeners are created or loaded from persistence.

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.on_registered"></a>

#### on_registered(channel, connection_id)

Keeps **channel**, to dispatch messages through it, and **connection_id**, to sign them.

* **Parameters:**
  * **channel** ([*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel) *[*[*SignedMessage*](entities.md#eric_sse.message.SignedMessage) *,* [*SignedMessage*](entities.md#eric_sse.message.SignedMessage) *]*)
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  None

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.set_action"></a>

#### set_action(name, action)

Hooks a callable to a string key.

Callables are selected when listener processes the message depending on its type.

They should return a list of MessageContract instances corresponding to response to action requested.

Reserved actions are ‘start’, ‘stop’.
Receiving a message with one of these types will fire corresponding action.

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **action** ([*Callable*](https://docs.python.org/3/library/typing.html#typing.Callable) *[* *[*[*SignedMessage*](entities.md#eric_sse.message.SignedMessage) *]* *,* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *[*[*MessageContract*](entities.md#eric_sse.message.MessageContract) *]* *]*)

<a id="eric_sse.prefabs.SimpleDistributedApplicationListener.dispatch_to"></a>

#### dispatch_to(receiver_id, msg)

Dispatches **msg** to connection **receiver_id**, signed with this listener’s connection id.

* **Parameters:**
  * **receiver_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
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

Bases: [`SSEChannel`](#eric_sse.prefabs.SSEChannel)[[`SignedMessage`](entities.md#eric_sse.message.SignedMessage), [`SignedMessage`](entities.md#eric_sse.message.SignedMessage)]

Channel for [`SimpleDistributedApplicationListener`](#eric_sse.prefabs.SimpleDistributedApplicationListener) instances.

Use a connections factory or repository that creates them, e.g.
`ChannelRepositoryBuilder(SimpleDistributedApplicationChannel).listeners(SimpleDistributedApplicationListener)`.

<a id="module-eric_sse.servers"></a>

<a id="prefab-servers-and-clients"></a>

## Prefab servers and clients

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
  **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  [*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel)

<a id="eric_sse.servers.ChannelContainer.rm"></a>

#### rm(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.servers.ChannelContainer.get_all_ids"></a>

#### get_all_ids()

* **Return type:**
  [*Iterable*](https://docs.python.org/3/library/typing.html#typing.Iterable)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]

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
    "r": "receiver (connection id when verb is 'rl')"
}
```

Possible values of **verb** identifies a supported action:

```default
"d" dispatch
"b" broadcast
"c" create channel
"r" add connection
"l" listen (opens a stream)
"w" watch (opens a stream)
"rl" remove a connection
"rc" remove a channel
```

See examples

<a id="eric_sse.servers.SocketServer.__init__"></a>

#### \_\_init_\_(file_descriptor_path, channels=None, channel_factory=<class 'eric_sse.prefabs.SSEChannel'>)

* **Parameters:**
  * **file_descriptor_path** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – See **start** method
  * **channels** ([*ChannelContainer*](#eric_sse.servers.ChannelContainer) *|* *None*) – the channels the server works on. A new empty container by default.
  * **channel_factory** ([*Callable*](https://docs.python.org/3/library/typing.html#typing.Callable) *[* *[* *]* *,* [*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel) *]*) – creates the channels requested by the ‘c’ verb, e.g.
    `lambda: repository.create({})` for channels built by a repository. Creates plain SSEChannel by default.

<a id="eric_sse.servers.SocketServer.start"></a>

#### *static* start(file_descriptor_path)

Shortcut to start a server given a file descriptor path

* **Parameters:**
  **file_descriptor_path** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – file descriptor path, all understood by [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path) is fine

<a id="eric_sse.servers.SocketServer.shutdown"></a>

#### *async* shutdown()

Graceful Shutdown: stops accepting connections, ends open streams and removes the socket file.
Returns when done, and so does **main**. Same as sending SIGINT or SIGTERM to the process.

<a id="eric_sse.servers.SocketServer.main"></a>

#### *async* main()

Starts the server. Returns after a shutdown.

<a id="module-eric_sse.clients"></a>

<a id="eric_sse.clients.SocketClient"></a>

### *class* SocketClient

A little facade to interact with SocketServer

<a id="eric_sse.clients.SocketClient.__init__"></a>

#### \_\_init_\_(file_descriptor_path)

* **Parameters:**
  **file_descriptor_path** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.send_payload"></a>

#### *async* send_payload(payload)

Send an arbitrary payload to a socket

see [`SocketServer`](#eric_sse.servers.SocketServer)

* **Parameters:**
  **payload** ([*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict))

<a id="eric_sse.clients.SocketClient.create_channel"></a>

#### *async* create_channel()

* **Return type:**
  [str](https://docs.python.org/3/builtins/stdtypes.html#str)

<a id="eric_sse.clients.SocketClient.register"></a>

#### *async* register(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.stream"></a>

#### *async* stream(channel_id, connection_id)

* **Return type:**
  [*AsyncIterable*](https://docs.python.org/3/library/typing.html#typing.AsyncIterable)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]

<a id="eric_sse.clients.SocketClient.broadcast_message"></a>

#### *async* broadcast_message(channel_id, message_type, payload)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **message_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **payload** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float))

<a id="eric_sse.clients.SocketClient.dispatch"></a>

#### *async* dispatch(channel_id, receiver_id, message_type, payload)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **receiver_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **message_type** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **payload** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict) *|* [*int*](https://docs.python.org/3/builtins/functions.html#int) *|* [*float*](https://docs.python.org/3/builtins/functions.html#float))

<a id="eric_sse.clients.SocketClient.remove_connection"></a>

#### *async* remove_connection(channel_id, connection_id)

* **Parameters:**
  * **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.clients.SocketClient.remove_channel"></a>

#### *async* remove_channel(channel_id)

* **Parameters:**
  **channel_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
