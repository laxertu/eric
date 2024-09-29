The lightweight library for async messaging nobody expects.
===========================================================

Installation
============
pip install eric-sse

Changelog
=========
0.4.0

Breaking changes:

* Rework of DataProcessingChannel, now extends AbstractChannel and its methods' signatures have been updated

* AbstractChannel.retry_timeout_milliseconds have been moved to SSEChannel

0.3.2

* Breaking change: now ThreadPoolListener callback only accepts Message as parameter
* Fixed a concurrency bug in ThreadPoolListener

Features
========
* Send to one listener and broadcast
* SSE format was adopted by design, is order to make library suitable for such kind of model
* Sockets
* Callbacks
* [**Experimental**] Threading support for large data processing


Possible applications

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See https://github.com/laxertu/eric-api

Trivia

Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric

Entities
========
.. automodule:: eric_sse.entities
    :members:

Prefab channels and listeners
=============================
.. automodule:: eric_sse.prefabs
    :members:


Prefab servers
==============
.. automodule:: eric_sse.servers
    :members:

Exceptions
==========
.. automodule:: eric_sse.exception
    :members:

Developers section
==================

Update README.md scipt: update_docs.sh
