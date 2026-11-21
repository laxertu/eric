Tutorials
=========

Two complete, runnable programs. Both live in the
`examples <https://github.com/laxertu/eric/tree/master/examples>`_ directory. The test suite runs them and compares
what they print with the output shown on their pages, so their code always works with the current version.

* :doc:`tutorial_in_memory`: a chat room where users subscribe, receive private and broadcast messages, and leave.
  Everything lives in the current process.
* :doc:`tutorial_kv_storage`: the same building blocks, persisted with SQLite, so channels, listeners and pending
  messages survive a restart.

.. toctree::
   :maxdepth: 1

   tutorial_in_memory
   tutorial_kv_storage
