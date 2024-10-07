<a id="the-lightweight-library-for-async-messaging-nobody-expects"></a>

# The lightweight library for async messaging nobody expects.

<a id="installation"></a>

# Installation

pip install eric-sse

<a id="features"></a>

# Features

* Send to one listener and broadcast
* SSE format was adopted by design, is order to make library suitable for such kind of model
* Sockets
* Callbacks
* [**Experimental**] Threading support for large data processing

**Possible applications**

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See [https://github.com/laxertu/eric-api](https://github.com/laxertu/eric-api)

**Trivia**

* Library name pretends to be a tribute to the following movie [https://en.wikipedia.org/wiki/Looking_for_Eric](https://en.wikipedia.org/wiki/Looking_for_Eric)

**Documentation**

* [Overview](docs.md)
* [Entities](docs.md#module-eric_sse.entities)
  * [`AbstractChannel`](docs.md#eric_sse.entities.AbstractChannel)
    * [`AbstractChannel.add_listener()`](docs.md#eric_sse.entities.AbstractChannel.add_listener)
    * [`AbstractChannel.broadcast()`](docs.md#eric_sse.entities.AbstractChannel.broadcast)
    * [`AbstractChannel.deliver_next()`](docs.md#eric_sse.entities.AbstractChannel.deliver_next)
    * [`AbstractChannel.dispatch()`](docs.md#eric_sse.entities.AbstractChannel.dispatch)
    * [`AbstractChannel.message_stream()`](docs.md#eric_sse.entities.AbstractChannel.message_stream)
    * [`AbstractChannel.notify_end()`](docs.md#eric_sse.entities.AbstractChannel.notify_end)
    * [`AbstractChannel.register_listener()`](docs.md#eric_sse.entities.AbstractChannel.register_listener)
  * [`Message`](docs.md#eric_sse.entities.Message)
  * [`MessageQueueListener`](docs.md#eric_sse.entities.MessageQueueListener)
    * [`MessageQueueListener.on_message()`](docs.md#eric_sse.entities.MessageQueueListener.on_message)
* [Prefab channels and listeners](docs.md#module-eric_sse.prefabs)
  * [`DataProcessingChannel`](docs.md#eric_sse.prefabs.DataProcessingChannel)
    * [`DataProcessingChannel.adapt()`](docs.md#eric_sse.prefabs.DataProcessingChannel.adapt)
    * [`DataProcessingChannel.process_queue()`](docs.md#eric_sse.prefabs.DataProcessingChannel.process_queue)
  * [`SSEChannel`](docs.md#eric_sse.prefabs.SSEChannel)
* [Prefab servers](docs.md#module-eric_sse.servers)
  * [`ChannelContainer`](docs.md#eric_sse.servers.ChannelContainer)
  * [`SocketServer`](docs.md#eric_sse.servers.SocketServer)
    * [`SocketServer.connect_callback()`](docs.md#eric_sse.servers.SocketServer.connect_callback)
    * [`SocketServer.shutdown()`](docs.md#eric_sse.servers.SocketServer.shutdown)
    * [`SocketServer.start()`](docs.md#eric_sse.servers.SocketServer.start)
* [Exceptions](docs.md#module-eric_sse.exception)
  * [`InvalidChannelException`](docs.md#eric_sse.exception.InvalidChannelException)
  * [`InvalidListenerException`](docs.md#eric_sse.exception.InvalidListenerException)
  * [`InvalidMessageFormat`](docs.md#eric_sse.exception.InvalidMessageFormat)
  * [`NoMessagesException`](docs.md#eric_sse.exception.NoMessagesException)
* [Changelog](docs.md#changelog)
* [Developers section](docs.md#developers-section)
