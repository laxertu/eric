<a id="error-handling"></a>

# Error handling

Errors raised by queues and listeners are passed to error handlers registered on the channel.
Then the channel either re-raises them or, where it swallows them (e.g. a listener’s `on_message`, or a push during a broadcast), logs them.

Handlers are not persisted: register them on each channel, or once on a
[`ChannelRepositoryBuilder`](reference/persistence.md#eric_sse.builder.ChannelRepositoryBuilder), that registers them on every channel it creates or loads.

```python
from eric_sse.handlers import ListenerErrorHandler

class AlertOnFailure(ListenerErrorHandler):
    def handle_on_message_error(self, connection_id, msg, exception):
        send_alert(f'{connection_id} failed on {msg.type}: {exception!r}')

channel.add_listener_error_handler(AlertOnFailure())
```

[`DataProcessingChannel`](reference/prefabs.md#eric_sse.prefabs.DataProcessingChannel) handles errors the same way, running listeners in an executor: listener
errors are handled in the channel’s process, and queue errors are re-raised after the messages already popped are
processed.

Subclasses that notify listeners their own way get the same behaviour by popping with
[`_pop_next()`](reference/entities.md#eric_sse.entities.AbstractChannel._pop_next) and passing listener errors to
[`_on_listener_error()`](reference/entities.md#eric_sse.entities.AbstractChannel._on_listener_error).

See [Queue patterns](queue_patterns.md) for handlers that implement common patterns, like Dead Letter.

<a id="stream-errors"></a>

# Stream errors

[`message_stream()`](reference/entities.md#eric_sse.entities.AbstractChannel.message_stream) doesn’t raise: it yields errors to the client, formatted by
[`adapt_error()`](reference/entities.md#eric_sse.entities.AbstractChannel.adapt_error), as messages are formatted by
[`adapt()`](reference/entities.md#eric_sse.entities.AbstractChannel.adapt).

* An [`InvalidConnectionException`](reference/exceptions.md#eric_sse.exception.InvalidConnectionException), an [`InvalidChannelException`](reference/exceptions.md#eric_sse.exception.InvalidChannelException)
  or a [`StoppedListenerException`](reference/exceptions.md#eric_sse.exception.StoppedListenerException) is yielded as it is, and the stream ends. A listener stopped while the stream waits ends it with no error: the stream notices it after
  the wait.
* Any other error is logged and yielded as an [`InternalStreamError`](reference/exceptions.md#eric_sse.exception.InternalStreamError), so that its details,
  e.g. a backend address, don’t reach clients. [`on_error()`](reference/entities.md#eric_sse.entities.AbstractChannel.on_error) decides whether the
  stream goes on, after a pause of [`wait_timeout_seconds`](reference/entities.md#eric_sse.entities.AbstractChannel.wait_timeout_seconds).

[`SSEChannel`](reference/prefabs.md#eric_sse.prefabs.SSEChannel) sends them as SSE events of type `error`:

```default
{
    "event": "error",
    "retry": 5,
    "data": {"error": "InternalStreamError", "message": "Internal error"}
}
```

Channels extending [`AbstractChannel`](reference/entities.md#eric_sse.entities.AbstractChannel) directly must implement `adapt_error`; override it in
prefab subclasses to change the format.

Timeouts are not errors: an idle stream waits [`wait_timeout_seconds`](reference/entities.md#eric_sse.entities.AbstractChannel.wait_timeout_seconds) for a
message, then checks whether its listener is still running. Each time, the wait ends with a
[`NoMessagesException`](reference/exceptions.md#eric_sse.exception.NoMessagesException), nothing is yielded, and the
[`on_wait_timeout()`](reference/entities.md#eric_sse.entities.AbstractChannel.on_wait_timeout) hook is called, e.g. to collect metrics or to end idle streams.

See [Error handlers](reference/handlers.md) for the classes.
