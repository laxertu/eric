Tutorials
=========

Two complete, runnable programs. Both live in the
`examples <https://github.com/laxertu/eric/tree/master/examples>`_ directory, and the test suite runs them,
so the code below always works with the current version.

In-memory application
---------------------

A chat room where users subscribe, receive private and broadcast messages, and leave.
Everything lives in the current process: no storage, no threads, no polling.

The main concepts:

* A **listener** (:class:`~eric_sse.listener.MessageQueueListener`) is a subscriber. Each listener has its own queue,
  and :meth:`~eric_sse.listener.MessageQueueListener.on_message` runs for every message delivered to it.
* A **channel** (here :class:`~eric_sse.prefabs.SSEChannel`) delivers messages to its listeners:
  :meth:`~eric_sse.entities.AbstractChannel.dispatch` sends to one listener,
  :meth:`~eric_sse.entities.AbstractChannel.broadcast` to all of them.
* :meth:`~eric_sse.entities.AbstractChannel.message_stream` streams the messages of one listener, adapted to the
  channel's output format. It's what a web server returns to each client. It starts the listener, waits for
  messages without consuming CPU, and ends when the listener is stopped.
* **Hooks** such as :meth:`~eric_sse.entities.AbstractChannel.on_listener_added` and
  :meth:`~eric_sse.entities.AbstractChannel.before_dispatch` customise a channel by subclassing. They do nothing by
  default.

.. literalinclude:: ../../examples/tutorial_in_memory.py
    :language: python

Output::

    [room] alice joined
    [room] bob joined
    [alice] private: hi alice, welcome!
    [alice] chat: hello everybody
    [bob] chat: hello everybody
    [alice] goodbye: None
    [room] alice left
    [bob] goodbye: None
    [room] bob left

Persistence with a custom KvStorage
-----------------------------------

The same building blocks, persisted with SQLite from the standard library, so channels, listeners and pending
messages survive an application restart.

The persistence layer needs two pieces from you:

* A :class:`~eric_sse.repository.KvStorage`: a key-value store with prefix search. The library stores everything it
  persists through it. Values are stored as they are, so serialisation (here ``pickle``) is up to the storage.
* A durable :class:`~eric_sse.queues.Queue`, if messages must survive a restart. Messages are not saved by the
  storage: a queue writes them itself on every push and pop. When the storage serialises a queue, only its
  identity should be saved. :class:`~eric_sse.queues.InMemoryQueue` can't be serialised at all, so it only works
  with storages that keep objects in process.

:class:`~eric_sse.builder.ChannelRepositoryBuilder` wires the rest. It gives channels, connections, listeners and
queues their own key prefix in one storage, and returns a channel repository.

Persistence is always explicit: ``create()`` only builds a channel, and ``persist()`` stores it with its
connections. ``dispatch()`` and ``broadcast()`` never need a ``persist()``.

A queue only has to implement ``pop(timeout)`` and ``push()``. The inherited
:meth:`~eric_sse.queues.Queue.wait_pop` runs ``pop`` in a worker thread, so streams never block the event loop.
Override it if your backend can wait asynchronously.

.. literalinclude:: ../../examples/tutorial_kv_storage.py
    :language: python

Output::

    First run: persisted channel 0801e78c-2985-44fd-92f3-6d0a0a20a3d3 and dispatched 2 messages
    Second run: loaded channel with retry timeout 1000 ms
      greeting: hello
      greeting: are you still there?
