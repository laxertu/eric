Verifying custom implementations
================================

Contracts are abstract test suites, shipped with the library, that describe what every implementation of a part has
to do. If you write your own part, e.g. a :class:`~eric_sse.repository.KvStorage` for your database, a contract tells
you whether it behaves as the library expects.

**An implementation is valid if all the tests of its contract pass.**

Available contracts
-------------------

* :class:`~eric_sse.contracts.repository.ChannelRepositoryContract`: channel repositories, whatever their storages,
  listeners, queues or custom repositories.

How to verify an implementation
-------------------------------

Every contract takes a :class:`~eric_sse.builder.ChannelRepositoryBuilder` as fixture, so you only need to write a
builder configured with your parts:

1. Subclass the contract together with ``unittest.TestCase``.
2. Implement ``create_builder()``, returning a builder that uses your parts. It is called once per test.
3. Implement ``channel_data()``, returning the data passed to the repository's ``create`` for the builder's channel
   class, without ``channel_id``.
4. Run it with your test runner, e.g. ``pytest test_my_storage.py``.

.. code-block:: python

    from unittest import TestCase

    from eric_sse.builder import ChannelRepositoryBuilder
    from eric_sse.contracts.repository import ChannelRepositoryContract
    from eric_sse.prefabs import SSEChannel

    from my_package import RedisStorage


    class RedisStorageTestCase(ChannelRepositoryContract, TestCase):
        def create_builder(self) -> ChannelRepositoryBuilder:
            return ChannelRepositoryBuilder(SSEChannel, RedisStorage())

        def channel_data(self) -> dict:
            return {'retry_timeout_milliseconds': 10}

Contracts are not ``TestCase`` themselves, so test runners do not collect the abstract suite.

Rules
-----

* **Start every test from empty storages.** Some tests check that a repository returns exactly what was persisted.
  With an external storage, either clean it in ``setUp`` / ``tearDown``, or have ``create_builder()`` return a builder
  over a new namespace (e.g. a random key prefix) each time.
* **Do not redefine or skip contract tests.** A skipped or redefined test is not a passed one, so the implementation
  cannot be considered valid.
* You can add your own tests to the same class: they do not affect the contract.

See :doc:`reference/contracts` for the contract classes.
