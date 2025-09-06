Reference
=========

.. image:: _static/overview.png
   :scale: 50 %


| thanks a lot https://excalidraw.com !!

**Introduction**

Eric is basically a toolkit for building async message management applications, paying special attention to Server Side Events based ones.
Its main components are:

* A core model with a set of abstractions and prefabs that give support to SSE and more.
* A persistence layer composed by a set of interfaces and base classes for building concrete layers

:class:`~eric_sse.connection.ConnectionsFactory` is shared between components. Persistence uses it to create objects after data fetch, while channels create connections when receiving new subscriptions.

**SSE in memory use case**

If you just want a simple, inmemory SSE service, base building blocks are available.
`Here <https://github.com/laxertu/eric/blob/master/examples/inmemory.py>`_ is a little demo

**Prefabs**

* :class:`~eric_sse.prefabs.SSEChannel` Server side Events support
* :class:`~eric_sse.prefabs.DataProcessingChannel` Launches parallel tasks when consuming queues and dispatches results to client who pushed them
* :class:`~eric_sse.prefabs.SimpleDistributedApplicationChannel` Acts like a Mediator between listeners that communicate each other




.. toctree::
   :maxdepth: 2
   :hidden:

   entities
   prefabs
   persistence
   exceptions


