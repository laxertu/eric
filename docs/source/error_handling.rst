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

Handlers
========

.. automodule:: eric_sse.handlers
    :members:
    :member-order: bysource


Queue patterns
==============

**Dead Letter**: :class:`~eric_sse.queue_patterns.DeadLetterHandler` pushes messages that could not be delivered or processed to a dead letter queue,
wrapped in a :class:`~eric_sse.queue_patterns.DeadLetter` that records the listener they were meant for and the error.

.. code-block:: python

    from eric_sse.prefabs import SSEChannel
    from eric_sse.builder import ChannelRepositoryBuilder
    from eric_sse.queue_patterns import DeadLetterHandler

    dead_letters = DeadLetterHandler()      # or DeadLetterHandler(a_persistent_queue)
    channels = (
        ChannelRepositoryBuilder(SSEChannel)
        .queuing_error_handler(dead_letters)
        .listener_error_handler(dead_letters)
        .build()
    )

    # later: inspect and redeliver
    dead_letter = dead_letters.queue.pop()
    print(dead_letter.listener_id, dead_letter.type, dead_letter.error)
    channel.dispatch(dead_letter.listener_id, dead_letter.message)

.. automodule:: eric_sse.queue_patterns
    :members:
    :show-inheritance:
    :member-order: bysource
