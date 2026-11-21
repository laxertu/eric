Queuing patterns
================

Common messaging patterns, in the ``eric_sse.queue_patterns`` module:

* :doc:`dead_letter`: messages that can't be delivered or processed go to a separate queue instead of being lost.
* :doc:`reliable_queue`: popped messages are kept until acknowledged, so they can be delivered again.

.. toctree::
   :maxdepth: 1

   dead_letter
   reliable_queue
