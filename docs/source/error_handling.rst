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

Handlers
========

.. automodule:: eric_sse.handlers
    :members:
    :member-order: bysource
