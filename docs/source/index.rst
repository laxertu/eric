# The lightweight library for async messaging nobody expects.
=======================================

Features

* Send to one listener and broadcast
* SSE format was adopted by design, is order to make library suitable for such kind of model
* Sockets
* Callbacks
* Threading support for large data processing

Possible applications

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See https://github.com/laxertu/eric-api

Trivia

Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric

Entities
========
.. automodule:: eric_sse.entities
    :members: Message, MessageQueueListener, AbstractChannel

Prefab channels and listeners
=============================
.. automodule:: eric_sse.entities
    :no-index:
    :members: SSEChannel, ThreadPoolListener


Prefab servers
==============
.. automodule:: eric_sse.servers
    :members: ChannelContainer, SocketServer

Exceptions
==========
.. automodule:: eric_sse.exception
    :members:
