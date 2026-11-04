Profiling
=========

The ``eric_sse.profiling`` module measures how much time queues and listeners take, without changing them:
:class:`~eric_sse.profiling.ProfiledQueue` and :class:`~eric_sse.profiling.ProfiledListener` wrap an existing queue or
listener, delegate every call to it, and record each call of its main methods in a
:class:`~eric_sse.profiling.CallStats`:

* ``calls``: number of calls, including the ones that raised;
* ``total_time``: their total time, in seconds;
* ``mean_time``: mean time per call, in seconds.

Stats are exposed by these getters:

* :class:`~eric_sse.profiling.ProfiledQueue`: ``push_stats``, ``pop_stats``, ``wait_pop_stats``;
* :class:`~eric_sse.profiling.ProfiledListener`: ``on_message_stats``.

**Usage**

.. code-block:: python

    from eric_sse.connection import Connection
    from eric_sse.prefabs import SSEChannel
    from eric_sse.profiling import ProfiledListener, ProfiledQueue
    from eric_sse.queues import InMemoryQueue

    channel = SSEChannel()
    queue = ProfiledQueue(InMemoryQueue())
    listener = ProfiledListener(MyListener())
    channel.register_connection(Connection(listener=listener, queue=queue))

    # ... dispatch and stream messages

    print(queue.push_stats.calls, queue.push_stats.mean_time)
    print(listener.on_message_stats.total_time)

A :class:`~eric_sse.profiling.ProfiledListener` has the same id as the listener it wraps, so it can be used in its
place. To profile the queues of every channel built by a repository, give the
:class:`~eric_sse.builder.ChannelRepositoryBuilder` a factory of profiled queues:

.. code-block:: python

    channels = (
        ChannelRepositoryBuilder(SSEChannel)
        .queues(lambda: ProfiledQueue(InMemoryQueue()))
        .build()
    )

**What is measured**

* Times include waiting: a :meth:`~eric_sse.queues.Queue.wait_pop`, or a :meth:`~eric_sse.queues.Queue.pop` with a
  timeout, lasts until a message arrives or the timeout expires. In a stream, ``wait_pop_stats`` includes idle time.
* Calls that raise are counted and timed too, e.g. empty pops, then the exception is re-raised.

For whole-scenario timings, see the benchmarks in the :doc:`devs`.

See :doc:`reference/profiling` for the classes.
