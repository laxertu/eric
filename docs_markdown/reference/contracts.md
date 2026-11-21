<a id="contracts"></a>

# Contracts

<a id="module-eric_sse.contracts.repository"></a>

<a id="repositories"></a>

## Repositories

<a id="eric_sse.contracts.repository.ChannelRepositoryContract"></a>

### *class* ChannelRepositoryContract

Use cases every channel repository has to satisfy, whatever its storages or custom repositories.

The fixture is a [`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder): to check a custom part, subclass this
together with `TestCase` and return a builder configured with it:

```default
class RedisStorageTestCase(ChannelRepositoryContract, TestCase):
    def create_builder(self):
        return ChannelRepositoryBuilder(SSEChannel, RedisStorage())

    def channel_data(self):
        return {'retry_timeout_milliseconds': 10}
```

Not a `TestCase` itself, so the abstract class is not collected.

<a id="eric_sse.contracts.repository.ChannelRepositoryContract.create_builder"></a>

#### *abstract* create_builder()

Returns the builder under test. Called once per test.

* **Return type:**
  [*ChannelRepositoryBuilder*](persistence.md#eric_sse.builder.ChannelRepositoryBuilder)

<a id="eric_sse.contracts.repository.ChannelRepositoryContract.channel_data"></a>

#### *abstract* channel_data()

Returns the data passed to the built repository’s `create` to create a channel of the builder’s
channel class. Without `channel_id`: tests that need a given id add it, the other ones need generated ids,
so that each call creates a different channel.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="module-eric_sse.contracts.channel"></a>

<a id="channels"></a>

## Channels

<a id="eric_sse.contracts.channel.ChannelContract"></a>

### *class* ChannelContract

Use cases every channel class has to satisfy: managing connections and delivering messages.

The fixture is a [`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder) for the channel class:

```default
class MyChannelTestCase(ChannelContract, IsolatedAsyncioTestCase):
    def create_builder(self):
        return ChannelRepositoryBuilder(MyChannel)

    def channel_data(self):
        return {}
```

Streamed events are compared with the channel’s own `adapt`, as their format is up to each channel.
Not a `TestCase` itself, so the abstract class is not collected.

<a id="eric_sse.contracts.channel.ChannelContract.create_builder"></a>

#### *abstract* create_builder()

Returns the builder under test. Called once per test.

* **Return type:**
  [*ChannelRepositoryBuilder*](persistence.md#eric_sse.builder.ChannelRepositoryBuilder)

<a id="eric_sse.contracts.channel.ChannelContract.channel_data"></a>

#### *abstract* channel_data()

Returns the data passed to the built repository’s `create`, see `ChannelRepositoryContract`.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="module-eric_sse.contracts.error_handling"></a>

<a id="error-handling"></a>

## Error handling

<a id="eric_sse.contracts.error_handling.ChannelErrorHandlingContract"></a>

### *class* ChannelErrorHandlingContract

Use cases every channel class has to satisfy when queues and listeners fail.

The fixture is a [`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder) for the channel class. Tests replace its
listeners and queues with failing ones where needed:

```default
class MyChannelTestCase(ChannelErrorHandlingContract, IsolatedAsyncioTestCase):
    def create_builder(self):
        return ChannelRepositoryBuilder(MyChannel)

    def channel_data(self):
        return {}
```

Not a `TestCase` itself, so the abstract class is not collected.

<a id="eric_sse.contracts.error_handling.ChannelErrorHandlingContract.create_builder"></a>

#### *abstract* create_builder()

Returns the builder under test. Called once per scenario.

* **Return type:**
  [*ChannelRepositoryBuilder*](persistence.md#eric_sse.builder.ChannelRepositoryBuilder)

<a id="eric_sse.contracts.error_handling.ChannelErrorHandlingContract.channel_data"></a>

#### *abstract* channel_data()

Returns the data passed to the built repository’s `create`, see `ChannelRepositoryContract`.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="module-eric_sse.contracts.queue"></a>

<a id="queues"></a>

## Queues

<a id="eric_sse.contracts.queue.QueueContract"></a>

### *class* QueueContract

Use cases every [`Queue`](entities.md#eric_sse.queues.Queue) implementation has to satisfy.

The fixture is a [`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder) creating queues of the class under test:

```default
class RedisQueueTestCase(QueueContract, IsolatedAsyncioTestCase):
    def create_builder(self):
        return ChannelRepositoryBuilder(SSEChannel).queues(RedisQueue)

    def channel_data(self):
        return {}
```

Not a `TestCase` itself, so the abstract class is not collected.

<a id="eric_sse.contracts.queue.QueueContract.create_builder"></a>

#### *abstract* create_builder()

Returns the builder under test. Called once per test.

* **Return type:**
  [*ChannelRepositoryBuilder*](persistence.md#eric_sse.builder.ChannelRepositoryBuilder)

<a id="eric_sse.contracts.queue.QueueContract.channel_data"></a>

#### *abstract* channel_data()

Returns the data passed to the built repository’s `create`, see `ChannelRepositoryContract`.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="module-eric_sse.contracts.reliable_queue"></a>

<a id="reliable-queues"></a>

## Reliable queues

<a id="eric_sse.contracts.reliable_queue.ReliableQueueContract"></a>

### *class* ReliableQueueContract

Use cases every [`ReliableQueue`](queue_patterns.md#eric_sse.queue_patterns.ReliableQueue) setup has to satisfy, whatever its inner queue
and in-flight storage.

The fixture is a [`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder) whose queues are reliable queues with the
given visibility timeout:

```default
class RedisReliableQueueTestCase(ReliableQueueContract, IsolatedAsyncioTestCase):
    def create_builder(self, visibility_timeout):
        return ChannelRepositoryBuilder(SSEChannel, RedisStorage()).queues(
            lambda: ReliableQueue(RedisQueue(), visibility_timeout=visibility_timeout, in_flight=RedisStorage())
        )

    def channel_data(self):
        return {}
```

Concrete classes must be `IsolatedAsyncioTestCase`, as some use cases are async.
Not a `TestCase` itself, so the abstract class is not collected.

<a id="eric_sse.contracts.reliable_queue.ReliableQueueContract.create_builder"></a>

#### *abstract* create_builder(visibility_timeout)

Returns the builder under test, creating reliable queues with **visibility_timeout**.

* **Parameters:**
  **visibility_timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float) *|* *None*)
* **Return type:**
  [*ChannelRepositoryBuilder*](persistence.md#eric_sse.builder.ChannelRepositoryBuilder)

<a id="eric_sse.contracts.reliable_queue.ReliableQueueContract.channel_data"></a>

#### *abstract* channel_data()

Returns the data passed to the built repository’s `create`, see `ChannelRepositoryContract`.

* **Return type:**
  [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)

<a id="module-eric_sse.contracts.doubles"></a>

<a id="test-doubles"></a>

## Test doubles

Test doubles used by contracts, e.g. parts that always fail and error handlers recording what they handle.

<a id="eric_sse.contracts.doubles.BrokenQueue"></a>

### *class* BrokenQueue

<a id="eric_sse.contracts.doubles.BrokenQueue.pop"></a>

#### pop(timeout=0)

Next message from the queue.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message. With 0 it returns immediately.
* **Return type:**
  [*MessageContract*](entities.md#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message is available, after waiting
**timeout** seconds.

<a id="eric_sse.contracts.doubles.BrokenQueue.wait_pop"></a>

#### *async* wait_pop(timeout)

Waits for the next message without blocking the event loop.

The default implementation runs [`pop()`](#eric_sse.contracts.doubles.BrokenQueue.pop) with **timeout** in a worker thread, so it takes one thread
per waiting call. Override it with a native async wait when possible.

* **Parameters:**
  **timeout** ([*float*](https://docs.python.org/3/builtins/functions.html#float)) – Seconds to wait for a message.
* **Return type:**
  [*MessageContract*](entities.md#eric_sse.message.MessageContract)

Raises a [`NoMessagesException`](exceptions.md#eric_sse.exception.NoMessagesException) if no message arrives within **timeout**.

<a id="eric_sse.contracts.doubles.BrokenListener"></a>

### *class* BrokenListener

<a id="eric_sse.contracts.doubles.BrokenListener.on_message"></a>

#### on_message(msg)

Event handler. It executes when a message is delivered to client

* **Parameters:**
  **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.contracts.doubles.RecordingQueuingErrorHandler"></a>

### *class* RecordingQueuingErrorHandler

<a id="eric_sse.contracts.doubles.RecordingQueuingErrorHandler.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.contracts.doubles.RecordingQueuingErrorHandler.handle_push_error"></a>

#### handle_push_error(connection_id, msg, exception)

Called when pushing **msg** to the queue of connection **connection_id** fails. The exception is re-raised afterwards.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))

<a id="eric_sse.contracts.doubles.RecordingQueuingErrorHandler.handle_pop_error"></a>

#### handle_pop_error(connection_id, exception)

Called when popping from the queue of connection **connection_id** fails. The exception is re-raised afterwards.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))

<a id="eric_sse.contracts.doubles.RecordingListenerErrorHandler"></a>

### *class* RecordingListenerErrorHandler

<a id="eric_sse.contracts.doubles.RecordingListenerErrorHandler.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.contracts.doubles.RecordingListenerErrorHandler.handle_on_message_error"></a>

#### handle_on_message_error(connection_id, msg, exception)

Called when [`on_message()`](entities.md#eric_sse.listener.MessageQueueListener.on_message) of connection **connection_id** fails.
The exception is not re-raised: **msg** is delivered anyway.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
