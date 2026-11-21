<a id="module-eric_sse.handlers"></a>

<a id="error-handlers"></a>

# Error handlers

<a id="eric_sse.handlers.QueuingErrorHandler"></a>

### *class* QueuingErrorHandler

Handles errors raised by queues, see [`add_queuing_error_handler()`](entities.md#eric_sse.entities.AbstractChannel.add_queuing_error_handler).

Methods do nothing by default: override the ones you need.

<a id="eric_sse.handlers.QueuingErrorHandler.handle_push_error"></a>

#### handle_push_error(connection_id, msg, exception)

Called when pushing **msg** to the queue of connection **connection_id** fails. The exception is re-raised afterwards.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.handlers.QueuingErrorHandler.handle_pop_error"></a>

#### handle_pop_error(connection_id, exception)

Called when popping from the queue of connection **connection_id** fails. The exception is re-raised afterwards.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None

<a id="eric_sse.handlers.ListenerErrorHandler"></a>

### *class* ListenerErrorHandler

Handles errors raised by listeners, see [`add_listener_error_handler()`](entities.md#eric_sse.entities.AbstractChannel.add_listener_error_handler).

Methods do nothing by default: override the ones you need.

<a id="eric_sse.handlers.ListenerErrorHandler.handle_on_message_error"></a>

#### handle_on_message_error(connection_id, msg, exception)

Called when [`on_message()`](entities.md#eric_sse.listener.MessageQueueListener.on_message) of connection **connection_id** fails.
The exception is not re-raised: **msg** is delivered anyway.

* **Parameters:**
  * **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
  * **msg** ([*MessageContract*](entities.md#eric_sse.message.MessageContract))
  * **exception** ([*Exception*](https://docs.python.org/3/builtins/exceptions.html#Exception))
* **Return type:**
  None
