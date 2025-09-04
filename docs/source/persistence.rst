Persistence
===========

.. image:: _static/persistence_layer_class_diagram.png
    :scale: 50 %


Base classes for channels and connections repositories.
The main idea is that a repository relies on some KV storage engine abstraction, and uses it and its correspondant composites repositories to build final objects to return.

To build a persistence layer is needed to provide an implementation to one or more of above abstractions, and use them to build a custom ChannelRepository

Base repositories
=================
.. automodule:: eric_sse.repository
    :undoc-members:
    :members:
    :show-inheritance:
    :member-order: bysource

Interoperability
================
.. automodule:: eric_sse.interfaces
    :members: ListenerRepositoryInterface, QueueRepositoryInterface, ConnectionRepositoryInterface, ChannelRepositoryInterface
    :undoc-members:
    :member-order: bysource
    :show-inheritance:
