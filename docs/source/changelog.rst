Changelog
=========
3.0.0 (unreleased)

* Docs: added Tutorials, with a complete in-memory example and a persistence one with a custom KvStorage (SQLite). Both are in examples/ and run by the test suite
* Added KvListenerRepository and KvQueueRepository to repository module
* FIX: SimpleDistributedApplicationListener.set_action now rejects reserved action names 'start' and 'stop'
* FIX: AbstractChannelRepository.delete no longer fails with InMemoryStorage when channel has connections
* KvStorage.fetch_by_prefix and fetch_all implementations must now tolerate deletions while results are iterated
* Added PrefixedStorage, a namespaced view of a KvStorage
* Listener and queue repositories now create the instances they persist: added create() to ListenerRepositoryInterface and QueueRepositoryInterface. KvListenerRepository accepts a listener_class, KvQueueRepository a queue_factory
* ConnectionRepositoryInterface is now a ConnectionsFactory: ConnectionRepository.create() delegates to listeners and queues repositories. create() methods never persist
* Channel repositories inject their connections repository as connections_factory into the channels they build. Removed connections_factory from AbstractChannelRepository constructor and ChannelRepositoryInterface
* Channels describe their own persisted state: added AbstractChannel.to_dict() and from_dict(). SSEChannel and DataProcessingChannel extend to_dict()
* AbstractChannelRepository and SSEChannelRepository replaced by a concrete ChannelRepository(storage, connections_repository, channel_class), covering every channel type. persist() raises a TypeError on channels of other classes
* DataProcessingChannel accepts channel_id and connections_factory
* Added ChannelRepositoryBuilder (builder module): wires channel, connections, listeners and queues repositories over one storage, with per-part overrides
* Connection, ConnectionsFactory, KvListenerRepository and KvQueueRepository are now generic on listener and queue types
* FIX: ConnectionRepository.load_all no longer returns connections of channels whose id starts with the given channel id
* Removed facade module
* KvQueueRepository and InMemoryQueue docs: a queue class decides what of its state is serialised; InMemoryQueue is in-process only
* Removed unused attribute from InMemoryQueue
* BREAKING: Queue.pop() accepts a timeout (seconds, default 0: return immediately). Queue implementations must accept it
* Added Queue.wait_pop(timeout), an async wait for the next message. The default runs pop() in a worker thread; InMemoryQueue waits natively, without threads or polling, and its push() wakes the waiting consumer from any thread. InMemoryQueue has a single consumer: concurrent wait_pop() calls on the same queue are not supported
* Added AbstractChannel.wait_next(listener_id, timeout), async counterpart of deliver_next()
* Added channel hooks, overridable methods that do nothing by default: on_listener_added, on_listener_removed, on_stream_start, on_stream_end, before_dispatch (transform or drop messages, broadcast included) and on_error (return False to end the stream)
* After an unexpected error, message_stream() waits wait_timeout_seconds before trying again, so a failing backend no longer makes it spin
* message_stream() starts the listener itself: no more listener.start() before streaming. Stopping the listener still ends the stream
* BREAKING: watch() is an async generator: use "async for m in channel.watch()". Its listener is removed when the stream ends
* Error messages yield by message_stream() have a serialisable payload, {'error': exception class name, 'message': str(exception)}, instead of the exception. The stream ends after an invalid listener or channel error, instead of repeating it forever
* add_listener() and register_listener() go through register_connection(), so subclasses can set up every new connection in one place
* FIX: SimpleDistributedApplicationChannel sets itself on listeners created by add_listener() or loaded from persistence, not only on register_listener(). dispatch_to() on a listener without channel raises an InvalidChannelException
* Added ConnectionRepositoryInterface.load_ids(channel_id): connection ids without loading listeners and queues. ChannelRepository.persist() and delete() use it, so they no longer load every listener and queue of the channel
* ChannelRepository.delete() is idempotent and no longer loads the channel
* message_stream waits for messages instead of polling, so idle streams no longer consume CPU. It checks whether its listener is still running every AbstractChannel.wait_timeout_seconds (default 1). stream_delay_seconds is now only an optional pause after each delivered message

2.1.1

* Added InvalidConnectionException and ItemNotFound to exceptions module
* Now InMemoryRepository raises an ItemNotFound on nonexistent key

2.1.0

* General rework of persistence layer. Removed some modules and introduced repository one.

1.5.5

Added get_channel method to ChannelRepositoryInterface

1.5.4

Removed eric-redis-queues as optional dependency

1.5.3

* Added kv_constructor_params_as_dict and kv_class_absolute_path to ObjectAsKeyValuePersistenceMixin
* FIX: SimpleDistributedApplicationListener now extends MessageQueueListener

1.5.2

* BREAKING: removed SSEChannel.payload_adapter
* Added connection repository class name to SSEChannel set of values in persistence.
* Minor: removed SSEChannel.create_from_dict

1.4.1

* Minor: updated AbstractChannel and SSEChannel constructor params order

1.3.0.1

* Fixed SimpleDistributedApplicationListener.register_listener signature

1.3.0

* BREAKING AbstractChannel.open renamed to load_persisted_data
* Fixed examples

1.2.0

* BREAKING register_listener now accepts a PersistableListener

1.1.0

Full persistence support

* added PersistableListener
* added PersistableConnection


**BREAKING**

* updated ConnectionRepositoryInterface's persistence methods, now they accept and return ConnectionRepositoryInterface instances
* AbstractChannel's add_listener and register listener now accept PersistableListener instances

1.0.0

* Rework of persistence layer support. Factories of queues have been replaced with connections repositories
* Moved MessageQueueListener to a separate module
* Removed _sync methods form MessageQueueListener
* Moved RepositoryError to exception module
* Prefabs dependencies were updated accordingly
* Benchmark module renamed to profile

0.7.9

* Channel and listener id generation now relies on uuid4

0.7.7

* Now SocketServer starts correspondant listener on 'l' command
* **BREAKING** DataProcessingChannel.process_queue and AbstractChannel.message_stream now cannot be awaited
* **BREAKING** Changed DataProcessingChannel.process_queue 'l' parameter changed to 'listener'


0.7.6

Added a get all channels' ids to sse container

0.7.5

* Removed eric redis queues references

0.7.4

* Added AbstractQueuesFactory injection support to SSEChannelContainer.add

0.7.3

* Fixed SSEChannelContainer.add and rm wrong exception thrown on no existent channel

0.7.2

* Invalid Channel or Listener Exception now yields an error message to client (no logs anymore)

0.7.0

* BREAKING: now Message's subclasses payload properties contains original payload

0.6.5

* Fixed UniqueMessage payload property, now behaviour is similar to SignedMessage


0.6.4.1

* Changed method's signature from Message to MessageContract

0.6.4

Breaking:

* Updated Message constructor signature

0.6.3

Breaking:

* General rework of model, if you are migrating to this version just update your namespaces accordingly
* Redis support added as extra


0.6.2

Breaking:

* Fixed property typo payload_adapter of SSEChannel
* Changed MESSAGE_TYPE_END_OF_STREAM value
* SimpleDistributedApplicationListener.on_message now requires a SignedMessage


0.6.1

* Added watch support to SocketClient
* Added payload_adapter to SSEChannel
* Added dispatch_to to SimpleDistributedApplicationListener


0.6.0.4

* Added more functionalities to SocketServer and SocketClient

0.6.0.2

* Improved logging format
* HTML documentation workflow


0.6.0

* Added SimpleDistributedApplicationListener
* ChannelContainerChannelContainer renamed to SSEChannelContainer
* Added SignedMessage entity

0.5.4.1

* Added SocketClient

0.5.3

* Restored behaviour of AbstractChannel.message_stream. Multiple streaming calls with same listener are allowed
* Added locking to queue pop

0.5.2

Fixed close stream too early in AbstractChannel.message_stream

0.5.1

AbstractChannel.message_stream raises and InvalidListenerException
if invoked more than one time with same listener

0.5.0.2

Fix: SSEChannel must accept stream_delay_seconds as constructor parameter

0.5.0

* Removed Threaded listener class
* Added DataProcessingChannel.process_queue


0.4.1.0

* Breaking: Changed DataProcessingChannel adapter to suit with SSE

0.4.0

Breaking changes:

* Rework of DataProcessingChannel, now extends AbstractChannel and its methods' signatures have been updated

* AbstractChannel.retry_timeout_milliseconds have been moved to SSEChannel

0.3.2

* Breaking change: now ThreadPoolListener callback only accepts Message as parameter
* Fixed a concurrency bug in ThreadPoolListener
