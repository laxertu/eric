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

_Last updated: 2026-10-25, branch `claude-md`._

### Done
- **Point 1: persistence wiring.**
  - Shipped `KvListenerRepository` and `KvQueueRepository`.
  - `AbstractChannelRepository.from_storage(storage_factory)` builds a fully wired repository in one call.
- **Point 2: single backend, partly done.**
  - `DefaultConnectionsFactory(listener_class, queue_factory)` declares listener and queue classes in one place, so most users no longer subclass `ConnectionsFactory`.
  - `Facade[L, Q]` (`eric_sse/facade.py`) persists channels, connections, listeners and queues in **one** `KvStorage` instance. Each gets its own namespace through `PrefixedStorage` (`channel:`, `connection:`, `listener:`, `queue:`).
  - `Connection`, `ConnectionsFactory`, `KvListenerRepository` and `KvQueueRepository` are generic on listener and queue types. They use `TypeVar`/`Generic` because the project supports Python 3.10.
- **Point 7: bugs.**
  - `set_action` now rejects the reserved names `start` and `stop`.
- **Bugs found along the way:**
  - `AbstractChannelRepository.delete` crashed with `InMemoryStorage` because it deleted while iterating. Fixed in `InMemoryStorage`, which now iterates over a snapshot.
  - `ConnectionRepository.load_all` matched channel ids by bare prefix, so channel `a` returned channel `ab`'s connections. It now searches `f'{channel_id}:'`.
- **Docs:** the changelog has a 3.0.0 (unreleased) section. Two generated class diagrams (`docs/eric_sse_pubsub_diagram.drawio`, `docs/eric_sse_persistence_diagram.drawio`) replace the old one. Regenerate them with `python docs/generate_class_diagrams.py`.

### Decisions
- **`KvStorage` contract:** `fetch_by_prefix` and `fetch_all` implementations must allow deletes while their results are iterated. Callers (e.g. `AbstractChannelRepository.delete`) stay lazy instead of copying results into a list.
- **Kv repositories store objects as they are.** Any serialisation is up to the `KvStorage` implementation.
- **The Facade covers wiring and lifecycle only** (channels, adding and removing listeners). `dispatch` and streaming stay on the channel object. After `channel.dispatch()`, callers must `facade.repository.persist(channel)` for storages that serialise. `InMemoryStorage` hides this because it stores references. When queues get written back will be settled with point 4.
- Breaking changes are acceptable while 3.0.0 is in alpha.

### Next
1. **Point 3: generic channel serialisation.** Channels describe their own state, so one `ChannelRepository` covers every channel type. This removes the need for `SSEChannelRepository` and the Facade's `repository_class` parameter. Also make all prefabs accept `channel_id` and `connections_factory` (`DataProcessingChannel` doesn't yet).
2. **Point 4: async waiting queues**, plus deciding when queues get persisted (see the Facade decision above).
3. Optional: a `KvStorage.delete_by_prefix`, so a backend can delete a channel's connections without loading them.
4. Points 5 and 6: lifecycle hooks, listener auto-start, `watch()` signature, serialisable error payloads, `set_channel` coupling.

### Open
- `docs/source/persistence.rst` embeds `_static/persistence_layer_class_diagram.png`, which is probably out of date. Replace it with an export of the new persistence diagram.
- The new diagrams' visual layout hasn't been checked, because there's no draw.io renderer on the dev machine.
