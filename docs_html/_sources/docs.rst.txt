Overview
========

.. toctree::
   :maxdepth: 2


.. image:: _static/overview.png
   :scale: 50 %
   :alt: thanks a lot https://excalidraw.com/ !!
   :align: right


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
0.6.0

* Added SimpleDistributedApplicationListener
* ChannelContainerChannelContainer renamed to SSEChannelContainer
* Added SignedMessage entity

0.5.4.1

* Added SocketClient

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

Update README.md script: update_docs.sh
