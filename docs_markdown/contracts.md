<a id="verifying-custom-implementations"></a>

# Verifying custom implementations

Contracts are abstract test suites, shipped with the library, that describe what every implementation of a part has
to do. If you write your own part, e.g. a [`KvStorage`](reference/persistence.md#eric_sse.repository.KvStorage) for your database, a contract tells
you whether it behaves as the library expects.

**An implementation is valid if all the tests of its contract pass.**

<a id="available-contracts"></a>

## Available contracts

Each contract is mixed with a test case class: `unittest.TestCase` or, when some of its use cases are async,
`unittest.IsolatedAsyncioTestCase`.

| Contract                                                                                                                | Verifies                                                                                                                                      | Test case class           |
|-------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| [`ChannelRepositoryContract`](reference/contracts.md#eric_sse.contracts.repository.ChannelRepositoryContract)           | Channel repositories, whatever their storages, listeners, queues or custom repositories                                                       | `TestCase`                |
| [`ChannelContract`](reference/contracts.md#eric_sse.contracts.channel.ChannelContract)                                  | Channel classes: managing connections and delivering messages                                                                                 | `IsolatedAsyncioTestCase` |
| [`ChannelErrorHandlingContract`](reference/contracts.md#eric_sse.contracts.error_handling.ChannelErrorHandlingContract) | Channel classes, when queues and listeners fail                                                                                               | `IsolatedAsyncioTestCase` |
| [`QueueContract`](reference/contracts.md#eric_sse.contracts.queue.QueueContract)                                        | [`Queue`](reference/entities.md#eric_sse.queues.Queue) implementations                                                                        | `IsolatedAsyncioTestCase` |
| [`ReliableQueueContract`](reference/contracts.md#eric_sse.contracts.reliable_queue.ReliableQueueContract)               | [`ReliableQueue`](reference/queue_patterns.md#eric_sse.queue_patterns.ReliableQueue) setups, whatever their inner queue and in-flight storage | `IsolatedAsyncioTestCase` |

[`eric_sse.contracts.doubles`](reference/contracts.md#module-eric_sse.contracts.doubles) holds the failing parts and recording error handlers the contracts use. You can
reuse them in your own tests.

<a id="how-to-verify-an-implementation"></a>

## How to verify an implementation

For a step by step guide, with the repository contract as example, see [How to test a custom channel repository](howto_repository.md).

Every contract takes a [`ChannelRepositoryBuilder`](reference/persistence.md#eric_sse.builder.ChannelRepositoryBuilder) as fixture, so you only need to write a
builder configured with your parts:

1. Subclass the contract together with its test case class.
2. Implement `create_builder()`, returning a builder that uses your parts. It is called once per test.
   `ReliableQueueContract.create_builder` also receives the visibility timeout to give your reliable queues.
3. Implement `channel_data()`, returning the data passed to the repository’s `create` for the builder’s channel
   class, without `channel_id`.
4. Run it with your test runner, e.g. `pytest test_my_storage.py`.

```python
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
```

Contracts are not `TestCase` themselves, so test runners do not collect the abstract suite.

<a id="rules"></a>

## Rules

* **Start every test from empty storages.** Some tests check that a repository returns exactly what was persisted.
  With an external storage, either clean it in `setUp` / `tearDown`, or have `create_builder()` return a builder
  over a new namespace (e.g. a random key prefix) each time.
* **Do not redefine or skip contract tests.** A skipped or redefined test is not a passed one, so the implementation
  cannot be considered valid.
* You can add your own tests to the same class: they do not affect the contract.

See [Contracts](reference/contracts.md) for the contract classes.
