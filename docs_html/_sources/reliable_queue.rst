Reliable Queue
==============

In the ``eric_sse.queue_patterns`` module.

With a plain queue, a message is gone once popped: if the consumer fails before handling it, e.g. the SSE client
disconnects, it's lost. :class:`~eric_sse.queue_patterns.ReliableQueue` keeps popped messages *in flight* until they
are acknowledged, so they can be delivered again. Delivery is *at least once*.

* :meth:`~eric_sse.queue_patterns.ReliableQueue.pop` and :meth:`~eric_sse.queue_patterns.ReliableQueue.wait_pop`
  return a :class:`~eric_sse.queue_patterns.ReliableMessage` and keep it in flight;
* :meth:`~eric_sse.queue_patterns.ReliableQueue.ack` removes it for good, once it's been handled;
* :meth:`~eric_sse.queue_patterns.ReliableQueue.nack` puts it back in the queue at once;
* a message not acknowledged within ``visibility_timeout`` seconds is put back in the queue by
  :meth:`~eric_sse.queue_patterns.ReliableQueue.requeue_expired`, that ``pop`` and ``wait_pop`` call before popping.
  With ``visibility_timeout=None`` it stays in flight until ``nack``.

Requeued messages go to the end of the queue.

**Usage**

.. code-block:: python

    from eric_sse.queue_patterns import ReliableQueue

    queue = ReliableQueue(visibility_timeout=30)
    queue.push(Message(msg_type='order', msg_payload={'id': 1}))

    msg = queue.pop()
    try:
        handle(msg.message)
        queue.ack(msg.id)
    except Exception:
        queue.nack(msg.id)

``ack`` and ``nack`` return ``False`` if the message isn't in flight: unknown id, already acknowledged, or already put
back in the queue because its visibility timeout expired. In the last case it will be delivered again.

**What is returned**

A :class:`~eric_sse.queue_patterns.ReliableMessage` wraps the pushed message and adds:

* ``id``: a new id to acknowledge it with, kept across redeliveries. It replaces the original message's id;
* ``deliveries``: how many times it has been popped. More than 1 means it is a redelivery;
* ``message``: the original message.

It is a message itself, with the original ``type`` and ``payload``.

**With channels**

A ``ReliableQueue`` is a :class:`~eric_sse.queues.Queue`, so a channel can use it for its connections, e.g. through a
custom :class:`~eric_sse.connection.ConnectionsFactory` or :meth:`~eric_sse.builder.ChannelRepositoryBuilder.queues`.
:class:`~eric_sse.prefabs.SSEChannel` sends the message id as the SSE ``id`` field, so a client can acknowledge what it
received, e.g. calling an endpoint of your application that calls ``ack``.

**Durability**

``ReliableQueue`` wraps a queue for messages waiting to be popped, and a :class:`~eric_sse.repository.KvStorage` for
in-flight ones. Both default to in-memory implementations. With durable ones, unacknowledged messages survive a restart:

.. code-block:: python

    queue = ReliableQueue(queue=my_durable_queue, visibility_timeout=30, in_flight=my_durable_storage)

It can be pickled if both can, so it can be persisted by a queue repository.

See :doc:`reference/queue_patterns` for the classes.
