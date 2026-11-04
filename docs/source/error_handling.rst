Error handling
==============

Errors raised by queues and listeners are passed to error handlers registered on the channel.
Then the channel either re-raises them or, where it swallows them (e.g. a listener's ``on_message``, or a push during a broadcast), logs them.

Handlers are not persisted: register them on each channel, or once on a
:class:`~eric_sse.builder.ChannelRepositoryBuilder`, that registers them on every channel it creates or loads.

.. code-block:: python

    from eric_sse.handlers import ListenerErrorHandler

    class AlertOnFailure(ListenerErrorHandler):
        def handle_on_message_error(self, listener_id, msg, exception):
            send_alert(f'{listener_id} failed on {msg.type}: {exception!r}')

    channel.add_listener_error_handler(AlertOnFailure())

See :doc:`queue_patterns` for handlers that implement common patterns, like Dead Letter.

Stream errors
=============

:meth:`~eric_sse.entities.AbstractChannel.message_stream` doesn't raise: it yields errors to the client, formatted by
:meth:`~eric_sse.entities.AbstractChannel.adapt_error`, as messages are formatted by
:meth:`~eric_sse.entities.AbstractChannel.adapt`.

* An invalid listener or channel error is yielded as it is, and the stream ends.
* Any other error is logged and yielded as an :class:`~eric_sse.exception.InternalStreamError`, so that its details,
  e.g. a backend address, don't reach clients. :meth:`~eric_sse.entities.AbstractChannel.on_error` decides whether the
  stream goes on, after a pause of :attr:`~eric_sse.entities.AbstractChannel.wait_timeout_seconds`.

:class:`~eric_sse.prefabs.SSEChannel` sends them as SSE events of type ``error``::

    {
        "event": "error",
        "retry": 5,
        "data": {"error": "InternalStreamError", "message": "Internal error"}
    }

Channels extending :class:`~eric_sse.entities.AbstractChannel` directly must implement ``adapt_error``; override it in
prefab subclasses to change the format.

Timeouts are not errors: an idle stream waits :attr:`~eric_sse.entities.AbstractChannel.wait_timeout_seconds` for a
message, then checks whether its listener is still running. Each time, the wait ends with a
:class:`~eric_sse.exception.TimeoutException`, nothing is yielded, and the
:meth:`~eric_sse.entities.AbstractChannel.on_wait_timeout` hook is called, e.g. to collect metrics or to end idle streams.

Handlers
========

.. automodule:: eric_sse.handlers
    :members:
    :member-order: bysource
