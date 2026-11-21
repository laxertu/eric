In-memory application
=====================

A chat room where users subscribe, receive private and broadcast messages, and leave.
Everything lives in the current process: no storage, no threads, no polling.

The main concepts:

* A **listener** (:class:`~eric_sse.listener.MessageQueueListener`) is what a subscriber does with messages:
  :meth:`~eric_sse.listener.MessageQueueListener.on_message` runs for every message delivered to it.
* A **connection** (:class:`~eric_sse.connection.Connection`) is a subscription: a listener and its own message
  queue, with an id. :meth:`~eric_sse.entities.AbstractChannel.register_listener` and
  :meth:`~eric_sse.entities.AbstractChannel.add_connection` subscribe to a channel and return the connection.
* A **channel** (here :class:`~eric_sse.prefabs.SSEChannel`) delivers messages to its connections:
  :meth:`~eric_sse.entities.AbstractChannel.dispatch` sends to one connection id,
  :meth:`~eric_sse.entities.AbstractChannel.broadcast` to all of them.
* :meth:`~eric_sse.entities.AbstractChannel.message_stream` streams the messages of one connection, adapted to the
  channel's output format. It's what a web server returns to each client. It starts the connection's listener, waits
  for messages without consuming CPU, and ends when the listener is stopped.
* **Hooks** such as :meth:`~eric_sse.entities.AbstractChannel.on_connection_added` and
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
