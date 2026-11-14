I agree. After reading the code, the basic case is easy: `SSEChannel()`, then `add_listener()`, then `dispatch()`. The trouble starts when someone wants persistence, a custom channel or a custom backend. These are the main problems, most important first.

### 1. Persistence takes too much wiring, and the needed parts aren't shipped
Getting a persisted `SSEChannel` means building 4 storages and 4 repositories, plus a factory (see `test/test_sse_channel_repository.py`). The tests also have to write their own `FakeListenerRepository` and `FakeQueueRepository`. Those are generic "store the object in a `KvStorage`" classes, so the library should provide them itself.
- **Fix:** ship `KvListenerRepository` and `KvQueueRepository`, plus one builder, e.g. `SSEChannelRepository.from_storage(storage_factory)`, so persistence takes one line.

### 2. The factory and the repositories must be kept in sync by hand
`ConnectionsFactory` creates queues and listeners, while `QueueRepositoryInterface` and `ListenerRepositoryInterface` load them. Nothing ties the two together. The `register_connection` docstring even warns about this (`eric_sse/entities.py:154`). Anyone writing a backend like `eric-redis-queues` has to implement both sides and match them.
- **Fix:** add a single `Backend` / `QueueBackend` concept that creates, persists and loads queues. The channel and the repository would both take that one object.

### 3. Every custom channel needs its own repository subclass
`AbstractChannelRepository` requires both `create()` and `_channel_to_dict()` for each channel type. For example, `DataProcessingChannel` can't be persisted at all. Its constructor (`eric_sse/prefabs.py:64`) doesn't accept `channel_id` or `connections_factory`.
- **Fix:** let channels describe their own state (`to_dict()` / `from_dict()` classmethod, or a declared list of constructor fields). One generic `ChannelRepository(channel_cls, ...)` would then cover every channel. Also make all prefabs accept `channel_id` and `connections_factory` consistently.

### 4. The streaming model polls instead of waiting
`message_stream` loops with `asyncio.sleep(stream_delay_seconds)` (`eric_sse/entities.py:127`). With the default of `0`, it spins the CPU while idle. Also, `Queue` has no way to wait for a message, so backends like Redis can't push messages and must be polled too.
- **Fix:** add an async `Queue.wait()` / `async pop(timeout)`, which matches the "timeouts" item in your TODO. The in-memory queue can use `asyncio.Queue`, and the stream loop can `await` it instead of sleeping.

### 5. Few extension points beyond `on_message` and `adapt`
There are no hooks for connect/disconnect, dispatch (middleware or filtering) or errors. Users who need any of these must subclass `AbstractChannel` and touch its internals, such as `_get_queue`.
- **Fix:** add a small set of channel hooks (`on_connect`, `on_disconnect`, `before_dispatch`, `on_error`) or a pluggable middleware list.

### 6. Some behaviour is easy to get wrong
- `add_listener()` returns a stopped listener, so callers must remember `listener.start()`. Forgetting it gives an empty stream with no error.
- `watch()` is an `async def` that returns an async iterator (`eric_sse/entities.py:197`). That forces `async for e in await channel.watch()`. It should be an async generator.
- Errors are sent as messages whose payload is the exception object itself (`eric_sse/entities.py:129`). That can't be serialised in SSE or over a socket.
- `SimpleDistributedApplicationListener` needs `set_channel()` before it works, which is a hidden coupling.

### 7. Bugs found along the way
- **The reserved-action check never fires:** `eric_sse/prefabs.py:141` checks `action in self.__internal_actions`, but it should check `name`. As a result, users can silently override `start` and `stop`.
- `facade.py` is an empty class. Either fill it in (it could be the one-line setup from point 1) or remove it.

### Suggested order
Since the next release is already at 3.0.0a0, breaking changes are fine now. I'd work in this order:
1. Points 1 and 2 (shipped KV repositories plus a single backend object). This gives the most benefit for the least change.
2. Point 3 (generic channel serialisation).
3. Point 4 (async waiting queues).

The rest are small cleanups. I can turn this into a plan or build the first item. I'd start with the `set_action` bug fix and the shipped KV repositories, with tests.

---

## Progress

_Last updated: 2026-11-05, branch `claude-md`._

### Done
- **Point 1: persistence wiring.**
  - Shipped `KvListenerRepository` and `KvQueueRepository`.
  - `AbstractChannelRepository.from_storage(storage_factory)` built a fully wired repository in one call. Replaced by `ChannelRepositoryBuilder` on 2026-11-01.
- **Point 2: single backend, partly done.**
  - `DefaultConnectionsFactory(listener_class, queue_factory)` declares listener and queue classes in one place, so most users no longer subclass `ConnectionsFactory`.
  - `PrefixedStorage` gives each repository its own namespace in one shared `KvStorage`.
  - The `Facade` was removed on 2026-11-01: a flat constructor with interdependent arguments, and it persisted implicitly. It will be replaced by repositories that create instances plus a Builder (see Decisions and Next).
  - `Connection`, `ConnectionsFactory`, `KvListenerRepository` and `KvQueueRepository` are generic on listener and queue types. They use `TypeVar`/`Generic` because the project supports Python 3.10.
- **Point 7: bugs.**
  - `set_action` now rejects the reserved names `start` and `stop`.
- **Bugs found along the way:**
  - `AbstractChannelRepository.delete` crashed with `InMemoryStorage` because it deleted while iterating. Fixed in `InMemoryStorage`, which now iterates over a snapshot.
  - `ConnectionRepository.load_all` matched channel ids by bare prefix, so channel `a` returned channel `ab`'s connections. It now searches `f'{channel_id}:'`.
- **Tutorials** (2026-11-01): `docs/source/tutorials.rst` includes `examples/tutorial_in_memory.py` (chat room, hooks) and `examples/tutorial_kv_storage.py` (SQLite `KvStorage` + durable `SqliteQueue`, simulated restart) via `literalinclude`. `test/test_examples.py` ran both until it was removed in `e11cabc`; see Open.
- **Docs:** the changelog has a 3.0.0 (unreleased) section. Two generated class diagrams (`docs/eric_sse_pubsub_diagram.drawio`, `docs/eric_sse_persistence_diagram.drawio`) replace the old one. Regenerate them with `python docs/generate_class_diagrams.py`.
- **Error handling** (2026-11-03):
  - `QueuingErrorHandler` and `ListenerErrorHandler` live on the channel. Every method receives the listener id first. Errors are re-raised after the handlers, or logged where the channel swallows them (e.g. `broadcast`).
  - Stream errors have their own path: the abstract `AbstractChannel.adapt_error(exception)`. Unexpected errors reach clients as an `InternalStreamError`, so internals don't leak.
  - `StoppedListenerException` (2026-11-05): `deliver_next` and `wait_next` raise it for a listener that isn't running, and `message_stream` yields it and ends. `NoMessagesException` only means an empty queue. Idle waits call the `on_wait_timeout` hook; they are not errors. (`TimeoutException` was tried and removed.)
  - `DataProcessingChannel.process_queue` (2026-11-05) uses the protected halves of `deliver_next`, `_pop_next` and `_on_listener_error`, so it no longer bypasses handlers and the stopped check.
- **Queue patterns** (`queue_patterns.py`, 2026-11-03):
  - Dead Letter: `DeadLetterHandler` plus the `DeadLetter` wrapper.
  - Reliable Queue: `ReliableQueue` plus `ReliableMessage`, with explicit `ack` / `nack` and a visibility timeout. In-flight messages live in a `KvStorage`.
- **Message id:** `MessageContract.id` defaults to `None`, and `SSEChannel.adapt` sends the SSE `id` field when a message has one. `UniqueMessage` was removed.
- **Generics** (2026-11-03/04):
  - `Queue[MIn, MOut]`, `InMemoryQueue[M]`, `MessageQueueListener[M]` and `AbstractChannel[MIn, MOut]` (the prefabs too).
  - `MIn` / `MOut` differ when a queue transforms messages (`ReliableQueue`).
  - There are no TypeVar defaults: both parameters are always written.
- **`MessageQueueListener.on_registered(channel)` hook** (2026-11-04): it replaces `set_channel` and the `isinstance` check in `SimpleDistributedApplicationChannel`. The distributed listener works on any channel.
- **Queue waits** (2026-11-04): fixed an `InMemoryQueue.wait_pop` race, where a message whose wake-up was still pending was lost at timeout.
- **Profiling** (`profiling.py`, 2026-11-04):
  - `ProfiledQueue` and `ProfiledListener` decorators, with stats in `CallStats`.
  - The Builder and `KvListenerRepository` take a `listener_factory` (2026-11-05), as queues already did, so wrapped listeners can be built through the Builder.
- **Benchmarks** (2026-11-04): pyperformance, as the optional Poetry group `benchmark`. `benchmarks/bm_builder_dispatch`: 10000 messages, with the Builder defaults.
- **Tests** (2026-11-05):
  - Rework towards use case tests, with a `ChannelRepositoryBuilder` fixture.
  - `ChannelRepositoryContract` (`eric_sse/contracts/repository.py`, since 2026-11-14 shipped with the library) is a reusable contract for custom storages and repositories.
  - `KvStorage.fetch_all` was removed.
- **Docs** (2026-11-04):
  - New pages: Error handling, Queue patterns and Profiling.
  - A Class reference section holds all generated docs, and the narrative page is now called Guide.
  - The README states semantic versioning from 3.0.0.

### Decisions
- **`KvStorage` contract:** `fetch_by_prefix` implementations must allow deletes while their results are iterated (`fetch_all` removed 2026-11-05: `fetch_by_prefix('')` returns all items). Callers (e.g. `AbstractChannelRepository.delete`) stay lazy instead of copying results into a list.
- **Kv repositories store objects as they are.** Any serialisation is up to the `KvStorage` implementation.
- **Persistence decisions belong to library clients.** The library never persists implicitly: `create()` methods only build objects, and clients call `persist` when they choose.
- **Persistence boundaries:**

  | Object | What gets persisted | Who triggers it |
  |---|---|---|
  | Channel | Configuration (`retry_timeout`…) and references to its connections | Client: `repository.persist(channel)` |
  | Listener | Its own state (e.g. `is_running`) | Client, through the channel repository |
  | Queue repository | The queue's identity and configuration (e.g. `queue_id`, Redis connection), **not its messages** | Client, through the channel repository |
  | Queue | Its messages, on every `push` and `pop` | The queue itself (e.g. `RedisQueue`) |

  So `dispatch` and `broadcast` never require a `persist`. An `InMemoryQueue` isn't durable, by design.
- **Repositories create the instances they persist.** `QueueRepositoryInterface.create()` and `ListenerRepositoryInterface.create()`. `ConnectionRepository` implements `ConnectionsFactory.create(listener=None)` by delegating to them, and the channel repository injects it into the channels it builds. Channels keep depending only on the narrow `ConnectionsFactory` interface, and `InMemoryConnectionsFactory` stays the default when nothing is persisted. This removes matching pairs such as factory plus repository: e.g. `RedisQueuesRepository` becomes the only place that knows `RedisQueue` and `BlockingRedisQueue`.
- **A Builder wires the repositories** and returns the channel repository. It never decides when to persist.
- **Error handlers are not persisted** (2026-11-03). They are runtime configuration: the Builder / `ChannelRepository` register them on every channel they create or load, so reloaded channels get them without storing them.
- Breaking changes are acceptable while 3.0.0 is in alpha.
- **No type checks as workarounds** (`isinstance`, `getattr`): if one seems needed, the design is wrong. Fix the contract instead: e.g. `MessageContract.id` instead of checking for `UniqueMessage`, and `on_registered` instead of checking the listener class.
- **Idle stream timeouts are not errors.** Yielding an error on every wait would flood idle clients, so they get a hook instead.
- **Subclasses reuse delivery steps, they don't copy them.** `AbstractChannel` exposes `_pop_next` and `_on_listener_error`, so custom delivery (e.g. in an executor) keeps the error handling.
- **Factories, not classes**, wherever the library creates objects (`listener_factory`, `queue_factory`): a class is one kind of factory, and wrappers need another.
- **`KvQueueRepository` keeps storing queues as they are** (2026-11-01). Each queue class decides what of its state is serialised: `RedisQueue` keeps only identity and configuration via `__getstate__`/`to_dict`. `InMemoryQueue` can't be pickled, so a serialising storage fails loudly instead of saving its messages; it is documented as in-process only and a test pins this. Storing only identity in the repository was rejected: with `InMemoryStorage`, `load` would return an empty queue and lose undelivered messages.

### Next
1. **Repositories create instances: done** (2026-11-01) in `eric_sse` and `eric-redis-queues` (branch `eric-3.0.0-migration`, commit `b83b36a`). Its `*ConnectionFactory` classes and Facade helper are gone, and `RedisSSEChannelRepository` takes `listener_class` and `queue_class`. Smoke-tested against a real Redis. Left to the user: `e2e_tests/load.py` still imports the removed factories.
2. **Builder: done in `eric_sse`** (2026-11-01): `eric_sse.builder.ChannelRepositoryBuilder`, with `channels()`, `connections()`, `listeners()`, `listeners_repository()`, `queues()`, `queues_repository()` and `build()`. Uses one default storage with `PrefixedStorage` namespaces, and a dedicated storage or repository can be given per part; the last call wins. `AbstractChannelRepository.from_storage` was removed in its favour, and the Builder is in the persistence class diagram.
3. **Point 3: generic channel serialisation: done in `eric_sse`** (2026-11-01). `AbstractChannel.to_dict()` / `from_dict(data, connections_factory)`; subclasses extend `to_dict()` via `super()`, and `from_dict` defaults to `cls(**data, ...)`. One concrete `ChannelRepository(storage, connections_repository, channel_class)` per channel type replaces `AbstractChannelRepository` and `SSEChannelRepository`; its `persist` rejects channels of another class (exact type, so a subclass isn't silently loaded as its parent). Builder: `.channels(channel_class, storage)`. `DataProcessingChannel` accepts `channel_id` and `connections_factory`. `eric-redis-queues` (`RedisSSEChannelRepository` extends the removed `SSEChannelRepository`) is deferred until `eric_sse` 3.0.0 is released (user's decision, 2026-11-01).
4. **Point 4: async waiting queues: done in `eric_sse`** (2026-11-01). Hybrid design, so that fully in-memory use stays non-blocking: `Queue.pop(timeout=0)` is the only thing a backend must implement; `Queue.wait_pop(timeout)` defaults to `asyncio.to_thread(self.pop, timeout)` (one thread per waiting stream); `InMemoryQueue` overrides it with a native async wait (waiter futures woken through `call_soon_threadsafe`, so `push` works from any thread). `AbstractChannel.wait_next()` is the async `deliver_next()`; `message_stream` awaits it with `wait_timeout_seconds` (class attribute, 1 s) to notice stopped listeners. `stream_delay_seconds` is only a rate limit now. Still to do with `eric-redis-queues` after 3.0.0: `pop` must accept `timeout`, and a native async `wait_pop` (e.g. `redis.asyncio` `blpop`) would avoid a thread per stream.
5. **Connection ids without loading: done** (2026-11-01). `KvStorage.delete_by_prefix` was dropped: listeners and queues are keyed by connection id in other namespaces, so they'd still need one delete each. The real cost was elsewhere: `ChannelRepository.persist()` loaded every listener and queue of the channel just to read connection ids (on every subscribe, with Redis), and `delete()` loaded them twice. Added `ConnectionRepositoryInterface.load_ids(channel_id)`, used by both; `delete()` is idempotent and no longer loads the channel.
6. **Point 6: done** (2026-11-01).
   - Listener auto-start: `message_stream()` starts the listener (every caller, `eric-api` included, called `start()` right before it; starting in `add_listener()` wouldn't help a listener reloaded after a disconnect). `stop()` still ends the stream.
   - `watch()` is an async generator and removes its listener when the stream ends.
   - Error payloads: `{'error': class name, 'message': str(e)}`. The stream now ends after an invalid listener/channel error: before, it yielded the same error forever. Unexpected errors still yield an error and go on, so a persistently failing backend (e.g. Redis down) still loops without pause: to be handled with point 5 (`on_error`) or a backoff.
   - `set_channel` coupling: `add_listener()`/`register_listener()` now go through `register_connection()`, which `SimpleDistributedApplicationChannel` overrides, so created and reloaded listeners get the channel too. Missing channel gives an `InvalidChannelException`.
7. **Point 5: hooks: done** (2026-11-01). Overridable `AbstractChannel` methods, no-op by default (chosen over a middleware list: simpler, consistent with `adapt()`/`on_message()`; a middleware list could be built on top):
   - `on_listener_added` / `on_listener_removed`: `add_listener()`, `register_listener()` / `remove_listener()`. Not fired by `register_connection()`, so reloading from persistence isn't a new subscription.
   - `on_stream_start` / `on_stream_end`: `message_stream()`, end fired on any exit, client disconnection included.
   - `before_dispatch(listener_id, msg)`: return a message or None to drop it; `broadcast()` included.
   - `on_error(listener, exc) -> bool`: unexpected stream errors, False ends the stream. The stream now pauses `wait_timeout_seconds` after an error, so a failing backend no longer spins.

#### Sketch: `eric-api` setup with the new API (names not final)
Today `eric-api` wires `RedisConnectionFactory`, `RedisConnectionRepository` and `RedisSSEChannelRepository` separately, and they must match.
```python
redis = RedisConnection(host=..., port=..., db=...)
channels = (
    ChannelRepositoryBuilder(storage=RedisStorage(PREFIX, redis))   # default storage, one namespace per repository
    .channels(SSEChannel)
    .listeners(MessageQueueListener)                                  # -> KvListenerRepository(..., listener_class=...)
    .queues(RedisQueuesRepository(redis))                             # creates and reloads RedisQueue
    .build()
)

# POST /channel/create
channel = channels.create({'channel_id': channel_id})
channels.persist(channel)

# POST /subscribe
channel = channels.load_one(channel_id)
listener = channel.add_listener()                          # queue created by RedisQueuesRepository
channels.persist(channel)

# POST /dispatch: no persist, RedisQueue.push writes the message
channel.dispatch(listener_id, msg)
```
`eric-redis-queues` could ship a one-line helper on top of this, e.g. `redis_channel_repository(redis, blocking=False)`.

### Open
- Side observation, for later: `eric-api` keeps its own cache sync on top of the library (`ChannelContainer`, `refresh_channels`, retry in `get_listener`).
- `docs/source/persistence.rst` embeds `_static/persistence_layer_class_diagram.png`, which is probably out of date. Replace it with an export of the new persistence diagram.
- The new diagrams' visual layout hasn't been checked, because there's no draw.io renderer on the dev machine.
- Class diagrams are regenerated only as the last step (user, 2026-11-05). The persistence diagram still shows `KvStorage.fetch_all`.
- `docs/source/tutorials.rst` says the test suite runs the tutorial examples, but `test/test_examples.py` was removed in `e11cabc`. Either restore a test, e.g. as a use case test, or reword the page.
- 9 mypy errors predate this work, in `servers.py`, `repository.py` and `prefabs.py`.
- Open question from the test rework: move the contract test classes into the package (e.g. `eric_sse/testing.py`), so library users can run them against their own parts.
- Generated `docs_html` and `docs_markdown` are rebuilt by `update_docs.sh` as the last step of the release.

### Pending design limits (found during the test rework, 2026-11-09)
- **`SocketServer` can't be given a channel class:** the `'c'` command always creates a plain `SSEChannel()`, so a socket client can't get a channel built by a repository. Injecting a channel factory through the constructor would fix it.
- **`SocketServer.cc` is a class attribute:** every server instance shares one `ChannelContainer`, and tests have to reset it around each run. It should be injected too.
- **`SocketServer` shutdown doesn't end open streams:** it handles SIGTERM with a graceful shutdown, so a stuck stream keeps the process alive and only `kill -9` stops it.
- **Running state lives on the listener:** `start()`, `stop()` and `is_running()` are really subscription state, so one listener can't be shared across connections (stopping it would stop them all). Listeners aren't pure behaviour yet.
- **The Builder can't mix queues on one channel:** one queue factory serves all connections, so tests with healthy and broken connections on the same channel fall back to `register_connection`.
- **Contracts repeat themselves:** all of them declare `channel_data()` and a create-a-channel step; a small shared base would remove that.
- **Examples aren't run by the suite:** `test/test_examples.py` no longer exists, though the changelog says the tutorials are run; `examples/tutorial_kv_storage.py` had broken unnoticed.
