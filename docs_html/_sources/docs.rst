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



.. toctree::
   :maxdepth: 2
   :hidden:

   entities
   prefabs
   persistence
   exceptions


