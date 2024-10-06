The lightweight library for async messaging nobody expects.
===========================================================

Installation
============
pip install eric-sse

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


Changelog
=========
0.5.3

* Restored behaviour of AbstractChannel.message_stream. Multiple streaming calls with same listener are allowed
* Added locking to queue pop

0.5.2

Fixed close stream too early in AbstractChannel.message_stream

0.5.1

AbstractChannel.message_stream raises and InvalidListenerException
if invoked more than one time with same listener

0.5.0.2

Fix: SSEChannel must accept stream_delay_seconds as constructor parameter

0.5.0

* Removed Threaded listener class
* Added DataProcessingChannel.process_queue


0.4.1.0

* Breaking: Changed DataProcessingChannel adapter to suit with SSE

0.4.0

Breaking changes:

* Rework of DataProcessingChannel, now extends AbstractChannel and its methods' signatures have been updated

* AbstractChannel.retry_timeout_milliseconds have been moved to SSEChannel

0.3.2

* Breaking change: now ThreadPoolListener callback only accepts Message as parameter
* Fixed a concurrency bug in ThreadPoolListener

Developers section
==================

Update README.md scipt: update_docs.sh
