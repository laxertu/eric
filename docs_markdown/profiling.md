<a id="module-eric_sse.profile"></a>

<a id="profiling-tools"></a>

# Profiling tools

<a id="eric_sse.profile.ListenerWrapper"></a>

### *class* ListenerWrapper

Bases: [`PersistableListener`](channels.md#eric_sse.listener.PersistableListener)

Wraps a listener to profile its on_message method.

<a id="eric_sse.profile.ListenerWrapper.__init__"></a>

#### \_\_init_\_(listener, profile_messages=False)

* **Parameters:**
  * **listener** ([*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener))
  * **profile_messages** (*bool*)

<a id="eric_sse.profile.ListenerWrapper.on_message"></a>

#### on_message(msg)

Performs on_message profiling

* **Parameters:**
  **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
* **Return type:**
  None

<a id="eric_sse.profile.DataProcessingChannelProfiler"></a>

### *class* DataProcessingChannelProfiler

Bases: `object`

<a id="eric_sse.profile.DataProcessingChannelProfiler.__init__"></a>

#### \_\_init_\_(channel)

Wraps a channel to profile its process_queue method.

* **Parameters:**
  **channel** ([*DataProcessingChannel*](prefabs.md#eric_sse.prefabs.DataProcessingChannel))

<a id="eric_sse.profile.DataProcessingChannelProfiler.add_listener"></a>

#### add_listener(listener)

Adds a listener to the channel after having wrapped it

* **Parameters:**
  **listener** ([*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener))
* **Return type:**
  [*ListenerWrapper*](#eric_sse.profile.ListenerWrapper)

<a id="eric_sse.profile.DataProcessingChannelProfiler.run"></a>

#### *async* run(listener)

Runs profile

* **Parameters:**
  **listener** ([*ListenerWrapper*](#eric_sse.profile.ListenerWrapper))
