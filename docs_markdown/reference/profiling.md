<a id="module-eric_sse.profiling"></a>

<a id="profiling"></a>

# Profiling

Profiling decorators for queues and listeners.

They wrap an existing queue or listener, delegate every call to it, and measure how many times its main methods
are called and how long they take:

```default
queue = ProfiledQueue(InMemoryQueue())
listener = ProfiledListener(MyListener())
channel.register_connection(Connection(listener=listener, queue=queue))
...
print(queue.push_stats.calls, queue.push_stats.total_time, listener.on_message_stats.mean_time)
```

<a id="eric_sse.profiling.CallStats"></a>

### *class* CallStats

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Number of calls of a method and the total time they took, in seconds. Calls that raise are counted too.

<a id="eric_sse.profiling.CallStats.__init__"></a>

#### \_\_init_\_()

* **Return type:**
  None

<a id="eric_sse.profiling.CallStats.record"></a>

#### record(elapsed)

Adds a call that took **elapsed** seconds.

* **Parameters:**
  **elapsed** ([*float*](https://docs.python.org/3/builtins/functions.html#float))
* **Return type:**
  None

<a id="eric_sse.profiling.CallStats.total_time"></a>

#### *property* total_time *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Total time of all calls, in seconds.

<a id="eric_sse.profiling.CallStats.mean_time"></a>

#### *property* mean_time *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Mean time per call, in seconds. 0 if there were no calls.

<a id="eric_sse.profiling.ProfiledQueue"></a>

### *class* ProfiledQueue

Bases: [`Queue`](entities.md#eric_sse.queues.Queue)[[`MIn`](entities.md#eric_sse.message.MIn), [`MOut`](entities.md#eric_sse.message.MOut)]

Wraps a queue and profiles its `push()`, [`pop()`](#eric_sse.profiling.ProfiledQueue.pop) and [`wait_pop()`](#eric_sse.profiling.ProfiledQueue.wait_pop).

Times include waiting: a [`wait_pop()`](#eric_sse.profiling.ProfiledQueue.wait_pop) or a [`pop()`](#eric_sse.profiling.ProfiledQueue.pop) with a timeout lasts until a message arrives,
or the timeout expires. Empty pops raising a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) are counted too.

* **Parameters:**
  **queue** ([*Queue*](entities.md#eric_sse.queues.Queue)) – The profiled queue.

<a id="eric_sse.profiling.ProfiledQueue.__init__"></a>

#### \_\_init_\_(queue)

* **Parameters:**
  **queue** ([*Queue*](entities.md#eric_sse.queues.Queue) *[*[*MIn*](entities.md#eric_sse.message.MIn) *,* [*MOut*](entities.md#eric_sse.message.MOut) *]*)
* **Return type:**
  None

<a id="eric_sse.profiling.ProfiledQueue.queue"></a>

#### *property* queue *: [Queue](entities.md#eric_sse.queues.Queue)[[MIn](entities.md#eric_sse.message.MIn), [MOut](entities.md#eric_sse.message.MOut)]*

The profiled queue.

<a id="eric_sse.profiling.ProfiledQueue.pop"></a>

#### pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*MOut*](entities.md#eric_sse.message.MOut)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available, after waiting
**timeout** seconds.

<a id="eric_sse.profiling.ProfiledQueue.wait_pop"></a>

#### *async* wait_pop(timeout)

Waits for the next message without blocking the event loop.

The default implementation runs [`pop()`](#eric_sse.profiling.ProfiledQueue.pop) with **timeout** in a worker thread, so it takes one thread
per waiting call. Override it with a native async wait when possible.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message.
* **Return type:**
  [*MOut*](entities.md#eric_sse.message.MOut)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="eric_sse.profiling.ProfiledListener"></a>

### *class* ProfiledListener

Bases: [`MessageQueueListener`](entities.md#eric_sse.listener.MessageQueueListener)[[`M`](entities.md#eric_sse.message.M)]

Wraps a listener and profiles its [`on_message()`](#eric_sse.profiling.ProfiledListener.on_message).

It delegates every other call to it.

* **Parameters:**
  **listener** ([*MessageQueueListener*](entities.md#eric_sse.listener.MessageQueueListener)) – The profiled listener.

<a id="eric_sse.profiling.ProfiledListener.__init__"></a>

#### \_\_init_\_(listener)

* **Parameters:**
  **listener** ([*MessageQueueListener*](entities.md#eric_sse.listener.MessageQueueListener) *[*[*M*](entities.md#eric_sse.message.M) *]*)
* **Return type:**
  None

<a id="eric_sse.profiling.ProfiledListener.listener"></a>

#### *property* listener *: [MessageQueueListener](entities.md#eric_sse.listener.MessageQueueListener)[[M](entities.md#eric_sse.message.M)]*

The profiled listener.

<a id="eric_sse.profiling.ProfiledListener.on_message"></a>

#### on_message(msg)

Event handler. It executes when a message is delivered to client

* **Parameters:**
  **msg** ([*M*](entities.md#eric_sse.message.M))
* **Return type:**
  None

<a id="eric_sse.profiling.ProfiledListener.on_registered"></a>

#### on_registered(channel, connection_id)

Hook called when the listener is registered to **channel**, through connection **connection_id**, see
[`register_connection()`](entities.md#eric_sse.entities.AbstractChannel.register_connection). Also called when a channel is loaded from
persistence. Does nothing by default: override it if the listener needs its channel or its address, e.g. to
dispatch messages.

* **Parameters:**
  * **channel** ([*AbstractChannel*](entities.md#eric_sse.entities.AbstractChannel) *[**Any* *,* [*M*](entities.md#eric_sse.message.M) *]*)
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
* **Return type:**
  None
