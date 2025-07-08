Overview
========

.. image:: _static/overview.png
   :scale: 50 %


thanks a lot https://excalidraw.com !!



Entities
========
.. automodule:: eric_sse.message
    :members:
    :show-inheritance:
    :member-order: bysource



Channels and listeners
======================
.. automodule:: eric_sse.entities
    :members: AbstractChannel
    :undoc-members:
    :member-order: bysource

.. automodule:: eric_sse.listener
    :members:
    :undoc-members:
    :exclude-members: __init__
    :member-order: bysource


Channel connections Management
==============================
.. automodule:: eric_sse.connection
    :members: Connection, AbstractConnectionRepository
    :member-order: bysource
    :show-inheritance:

Prefab channels and listeners
=============================
.. automodule:: eric_sse.prefabs
    :undoc-members:
    :exclude-members: set_channel
    :members:
    :show-inheritance:
    :member-order: bysource


Prefab servers and clients
==========================
.. automodule:: eric_sse.servers
    :members:
    :undoc-members:
    :exclude-members: cc, ACK, connect_callback, handle_command
    :member-order: bysource

.. automodule:: eric_sse.clients
    :undoc-members:
    :members:
    :member-order: bysource

Queues
======
.. automodule:: eric_sse.queue
    :undoc-members:
    :members: Queue
    :member-order: bysource
    :show-inheritance:

Exceptions
==========
.. automodule:: eric_sse.exception
    :members:

Profiling tools
==================
.. automodule:: eric_sse.profile
    :members:
    :undoc-members:
    :member-order: bysource
    :show-inheritance:
