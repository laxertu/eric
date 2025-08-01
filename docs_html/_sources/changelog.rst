Changelog
=========

1.5.1

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
