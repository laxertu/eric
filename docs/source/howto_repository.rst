How to test a custom channel repository
=======================================

You wrote your own persistence part, e.g. a :class:`~eric_sse.repository.KvStorage` for your database, or a
listeners or queues repository, and you want to know whether eric can rely on it. Test it against
:class:`~eric_sse.contracts.repository.ChannelRepositoryContract`: the use cases every channel repository has to
satisfy, whatever its parts. Your part is valid when all of them pass.

The library tests its own :class:`~eric_sse.repository.InMemoryStorage` this way, and so will you.

1. Start from the library's test case
-------------------------------------

This is the whole test of :class:`~eric_sse.repository.InMemoryStorage`:

.. literalinclude:: ../../test/test_repository_contract.py
    :language: python

You extend :class:`~eric_sse.contracts.repository.ChannelRepositoryContract` together with ``unittest.TestCase``,
and implement two methods:

* ``create_builder()`` returns a :class:`~eric_sse.builder.ChannelRepositoryBuilder` that uses your part. The
  contract builds the repository under test from it, once per test.
* ``channel_data()`` returns the data the repository's ``create`` needs to create a channel of the builder's channel
  class. Leave ``channel_id`` out: the tests that need given ids add them.

The contract is not a ``TestCase`` itself, so your test runner only collects your class.

2. Put your part in the builder
-------------------------------

Write the same class for your part. What ``create_builder()`` returns depends on what you replace:

.. code-block:: python

    from unittest import TestCase

    from eric_sse.builder import ChannelRepositoryBuilder
    from eric_sse.contracts.repository import ChannelRepositoryContract
    from eric_sse.prefabs import SSEChannel

    from my_package import MyStorage


    class MyStorageTestCase(ChannelRepositoryContract, TestCase):
        def create_builder(self) -> ChannelRepositoryBuilder:
            # A storage for everything: channels, connections, listeners and queues
            return ChannelRepositoryBuilder(SSEChannel, MyStorage())

        def channel_data(self) -> dict:
            return {'retry_timeout_milliseconds': 10}

To test only some parts, keep the defaults for the others and give the builder yours:

* ``.channels(storage)`` or ``.connections(storage)``: a storage for channels or connections only;
* ``.listeners_repository(repository)`` or ``.queues_repository(repository)``: your own listeners or queues
  repository;
* ``.listeners(factory)`` or ``.queues(factory)``: the listeners or queues your repositories create, e.g. a durable
  queue.

If you persist your own channel class, build with it, ``ChannelRepositoryBuilder(MyChannel, ...)``, and return its
constructor arguments from ``channel_data()``.

3. Start every test from empty storage
--------------------------------------

Some use cases check that the repository returns *exactly* what was persisted, so leftovers of a previous test make
them fail. ``InMemoryStorage`` is new for every test. With a database or a file, clean up around each test:

.. code-block:: python

    class MyStorageTestCase(ChannelRepositoryContract, TestCase):
        def setUp(self):
            self.database = create_test_database()

        def tearDown(self):
            self.database.drop()

        def create_builder(self) -> ChannelRepositoryBuilder:
            return ChannelRepositoryBuilder(SSEChannel, MyStorage(self.database))

If cleaning up is not possible, e.g. a shared server, give each builder its own namespace instead, such as a random
key prefix.

4. Run it
---------

Run it as any other test::

    pytest test_my_storage.py

and a single use case with::

    pytest test_my_storage.py::MyStorageTestCase::test_deleting_a_channel_twice_does_not_fail

5. Read the failures
--------------------

Each test is a use case, and its name says what your part must do:

.. list-table::
   :header-rows: 1

   * - Test
     - What it requires
   * - ``test_persisted_channels_are_returned_by_load_all_and_load_one``
     - Persisted channels can be loaded, all together or by id, and nothing else is returned.
   * - ``test_channel_configuration_is_returned_after_reload``
     - A reloaded channel has the configuration it was persisted with.
   * - ``test_registered_listeners_are_returned_after_reload``
     - A reloaded channel has the connections it was persisted with.
   * - ``test_persisted_connection_parts_are_returned_by_their_repositories``
     - A persisted connection, its listener and its queue, pending messages included, can be loaded back.
   * - ``test_messages_are_kept_per_listener``
     - Pending messages are kept for their own connection only.
   * - ``test_connections_removed_from_a_channel_are_deleted_on_persist``
     - Persisting a channel deletes the connections removed from it, listeners and queues included.
   * - ``test_deleting_a_channel_deletes_all_its_connections``
     - Deleting a channel deletes its connections, listeners and queues too.
   * - ``test_deleting_a_channel_twice_does_not_fail``
     - Deleting is idempotent.
   * - ``test_channels_whose_ids_share_a_prefix_do_not_mix``
     - Channels ``a`` and ``ab`` keep their own connections.
   * - ``test_channel_ids_containing_the_key_separator_do_not_mix``
     - Channels ``a`` and ``a:b`` keep their own connections.

**Common causes**

* **A missing key raises the wrong error.** :meth:`~eric_sse.repository.KvStorage.fetch_one` must raise
  :class:`~eric_sse.exception.ItemNotFound`, not your database's own error, e.g. a ``KeyError``.
* **Deleting a missing key raises.** :meth:`~eric_sse.repository.KvStorage.delete` must do nothing instead.
* **Deletions break a running search.** Repositories delete keys while iterating the results of
  :meth:`~eric_sse.repository.KvStorage.fetch_by_prefix`, so it must not iterate over a live view of your data, e.g.
  collect the keys first.
* **Queues can't be stored.** If your storage serialises values, e.g. with ``pickle``, the default
  :class:`~eric_sse.queues.InMemoryQueue` fails, as it can only live in memory. Give the builder a durable queue with
  ``.queues(factory)``, that stores its messages itself, and test it with
  :class:`~eric_sse.contracts.queue.QueueContract`. See the ``SqliteQueue`` of the :doc:`tutorials` for an example.

6. Keep it in your suite
------------------------

Once everything passes, keep the test case in your suite: it checks your part against every new eric release.
You can add your own tests to the same class, they don't affect the contract. Don't redefine or skip contract tests:
a skipped test is not a passed one.

See :doc:`contracts` for the other contracts, e.g. for your own queues or channels.
