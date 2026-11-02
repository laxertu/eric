<a id="tutorials"></a>

# Tutorials

Two complete, runnable programs. Both live in the
[examples](https://github.com/laxertu/eric/tree/master/examples) directory, and the test suite runs them,
so the code below always works with the current version.

<a id="in-memory-application"></a>

## In-memory application

A chat room where users subscribe, receive private and broadcast messages, and leave.
Everything lives in the current process: no storage, no threads, no polling.

The main concepts:

* A **listener** ([`MessageQueueListener`](entities.md#eric_sse.listener.MessageQueueListener)) is a subscriber. Each listener has its own queue,
  and [`on_message()`](entities.md#eric_sse.listener.MessageQueueListener.on_message) runs for every message delivered to it.
* A **channel** (here [`SSEChannel`](prefabs.md#eric_sse.prefabs.SSEChannel)) delivers messages to its listeners:
  [`dispatch()`](entities.md#eric_sse.entities.AbstractChannel.dispatch) sends to one listener,
  [`broadcast()`](entities.md#eric_sse.entities.AbstractChannel.broadcast) to all of them.
* [`message_stream()`](entities.md#eric_sse.entities.AbstractChannel.message_stream) streams the messages of one listener, adapted to the
  channel’s output format. It’s what a web server returns to each client. It starts the listener, waits for
  messages without consuming CPU, and ends when the listener is stopped.
* **Hooks** such as [`on_listener_added()`](entities.md#eric_sse.entities.AbstractChannel.on_listener_added) and
  [`before_dispatch()`](entities.md#eric_sse.entities.AbstractChannel.before_dispatch) customise a channel by subclassing. They do nothing by
  default.

```python
"""
Tutorial: a complete in-memory application.

A chat room where users subscribe, receive private and broadcast messages, and leave.
Everything lives in the current process: no storage, no threads, no polling.

Run it with: python examples/tutorial_in_memory.py
"""
import asyncio

from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SSEChannel


# 1. A listener receives messages. Override on_message to react to each delivered message.
class ChatUser(MessageQueueListener):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def on_message(self, msg: MessageContract) -> None:
        # Leaving the room is just a message: stopping the listener ends its stream
        if msg.type == 'goodbye':
            self.stop()


# 2. A channel delivers messages to its listeners. Hooks let you customise it without touching its internals.
class ChatRoom(SSEChannel):

    def on_listener_added(self, listener: MessageQueueListener) -> None:
        print(f'[room] {listener.name} joined')

    def on_stream_end(self, listener: MessageQueueListener) -> None:
        print(f'[room] {listener.name} left')

    def before_dispatch(self, listener_id: str, msg: MessageContract) -> MessageContract | None:
        # Drop messages with forbidden words; returning None discards the message
        if 'spam' in str(msg.payload):
            return None
        return msg


async def user_session(room: ChatRoom, user: ChatUser):
    """What a web server does for each client: stream the channel's output for that listener."""
    # message_stream starts the listener, waits for messages without consuming CPU, and ends when the listener stops.
    # SSEChannel adapts every message to an SSE event: {'event': ..., 'retry': ..., 'data': ...}
    async for event in room.message_stream(user):
        print(f'[{user.name}] {event["event"]}: {event["data"]}')


async def main():
    room = ChatRoom()

    # 3. Subscribe: register existing listeners (add_listener() would create a plain MessageQueueListener instead)
    alice, bob = ChatUser('alice'), ChatUser('bob')
    room.register_listener(alice)
    room.register_listener(bob)

    # 4. Messages can be dispatched before streams start: they wait in each listener's queue
    room.dispatch(alice.id, Message(msg_type='private', msg_payload='hi alice, welcome!'))

    # 5. Stream to every user concurrently
    sessions = [asyncio.create_task(user_session(room, user)) for user in (alice, bob)]
    await asyncio.sleep(0.1)

    room.broadcast(Message(msg_type='chat', msg_payload='hello everybody'))
    room.broadcast(Message(msg_type='chat', msg_payload='buy spam now'))  # Dropped by before_dispatch
    await asyncio.sleep(0.1)

    # 6. Leave: each listener stops on its 'goodbye' message, its stream ends, and the listener is removed
    room.broadcast(Message(msg_type='goodbye'))
    await asyncio.gather(*sessions)
    for user in (alice, bob):
        room.remove_listener(user.id)


if __name__ == '__main__':
    asyncio.run(main())
```

Output:

```default
[room] alice joined
[room] bob joined
[alice] private: hi alice, welcome!
[alice] chat: hello everybody
[bob] chat: hello everybody
[alice] goodbye: None
[room] alice left
[bob] goodbye: None
[room] bob left
```

<a id="persistence-with-a-custom-kvstorage"></a>

## Persistence with a custom KvStorage

The same building blocks, persisted with SQLite from the standard library, so channels, listeners and pending
messages survive an application restart.

The persistence layer needs two pieces from you:

* A [`KvStorage`](persistence.md#eric_sse.repository.KvStorage): a key-value store with prefix search. The library stores everything it
  persists through it. Values are stored as they are, so serialisation (here `pickle`) is up to the storage.
* A durable [`Queue`](entities.md#eric_sse.queues.Queue), if messages must survive a restart. Messages are not saved by the
  storage: a queue writes them itself on every push and pop. When the storage serialises a queue, only its
  identity should be saved. [`InMemoryQueue`](entities.md#eric_sse.queues.InMemoryQueue) can’t be serialised at all, so it only works
  with storages that keep objects in process.

[`ChannelRepositoryBuilder`](persistence.md#eric_sse.builder.ChannelRepositoryBuilder) wires the rest. It gives channels, connections, listeners and
queues their own key prefix in one storage, and returns a channel repository.

Persistence is always explicit: `create()` only builds a channel, and `persist()` stores it with its
connections. `dispatch()` and `broadcast()` never need a `persist()`.

A queue only has to implement `pop(timeout)` and `push()`. The inherited
[`wait_pop()`](entities.md#eric_sse.queues.Queue.wait_pop) runs `pop` in a worker thread, so streams never block the event loop.
Override it if your backend can wait asynchronously.

```python
"""
Tutorial: persistence with a custom KvStorage.

Channels, listeners and messages survive an application restart, using SQLite from the standard library.
Two classes are needed:

- SqliteStorage: a KvStorage. The library stores everything it persists through it (channels configuration,
  connections, listeners, queues identity), each kind of object under its own key prefix.
- SqliteQueue: a durable Queue. Messages are not persisted by the storage: a queue writes them itself on every
  push and pop, so dispatch and broadcast never require a persist.

Run it with: python examples/tutorial_kv_storage.py
"""
import asyncio
import pickle
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable

from eric_sse import generate_uuid
from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.exception import ItemNotFound, NoMessagesException
from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SSEChannel
from eric_sse.queues import Queue
from eric_sse.repository import KvStorage


def connect(db_path: str) -> sqlite3.Connection:
    # One connection per operation: simple, and safe when a queue is used from worker threads (see Queue.wait_pop)
    return sqlite3.connect(db_path, isolation_level=None)


class SqliteStorage(KvStorage):
    """Values are pickled, so any picklable object can be stored."""

    def __init__(self, db_path: str):
        self.__db_path = db_path
        with closing(connect(db_path)) as db:
            db.execute('CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value BLOB)')

    def __query(self, sql: str, params: tuple = ()) -> list[tuple]:
        with closing(connect(self.__db_path)) as db:
            return db.execute(sql, params).fetchall()

    def fetch_by_prefix(self, prefix: str) -> Iterable[Any]:
        # Results are fetched all at once, so callers can delete keys while iterating (a KvStorage requirement)
        rows = self.__query('SELECT value FROM kv WHERE substr(key, 1, ?) = ?', (len(prefix), prefix))
        return [pickle.loads(value) for (value,) in rows]

    def fetch_all(self) -> Iterable[Any]:
        return [pickle.loads(value) for (value,) in self.__query('SELECT value FROM kv')]

    def upsert(self, key: str, value: Any):
        self.__query('INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)', (key, pickle.dumps(value)))

    def fetch_one(self, key: str) -> Any:
        rows = self.__query('SELECT value FROM kv WHERE key = ?', (key,))
        if not rows:
            raise ItemNotFound(key=key)
        return pickle.loads(rows[0][0])

    def delete(self, key: str):
        self.__query('DELETE FROM kv WHERE key = ?', (key,))


class SqliteQueue(Queue):
    """
    A durable queue. When the storage pickles it, only its identity (database path and queue id) is saved:
    its messages stay in the messages table.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue_id = generate_uuid()
        with closing(connect(db_path)) as db:
            db.execute(
                'CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, queue_id TEXT, message BLOB)'
            )

    def push(self, message: MessageContract) -> None:
        with closing(connect(self.db_path)) as db:
            db.execute('INSERT INTO messages (queue_id, message) VALUES (?, ?)', (self.queue_id, pickle.dumps(message)))

    def pop(self, timeout: float = 0) -> MessageContract:
        deadline = time.monotonic() + timeout
        while True:
            with closing(connect(self.db_path)) as db:
                db.execute('BEGIN IMMEDIATE')  # Locks the database, so two consumers can't pop the same message
                row = db.execute(
                    'SELECT id, message FROM messages WHERE queue_id = ? ORDER BY id LIMIT 1', (self.queue_id,)
                ).fetchone()
                if row is not None:
                    db.execute('DELETE FROM messages WHERE id = ?', (row[0],))
                db.execute('COMMIT')
            if row is not None:
                return pickle.loads(row[1])
            if time.monotonic() >= deadline:
                raise NoMessagesException
            time.sleep(0.05)
    # wait_pop() is inherited: it runs pop() with a timeout in a worker thread, so the event loop is never blocked.


def build_repository(db_path: str):
    # One storage for everything: the builder gives channels, connections, listeners and queues their own key prefix.
    # The default queues repository stores queues as they are; queue_factory decides which queues channels create.
    return (
        ChannelRepositoryBuilder(SqliteStorage(db_path))
        .channels(SSEChannel)
        .queues(queue_factory=lambda: SqliteQueue(db_path))
        .build()
    )


def first_run(db_path: str) -> tuple[str, str]:
    """Creates and persists a channel with one listener, then dispatches messages."""
    repository = build_repository(db_path)

    # Nothing is persisted implicitly: create() only builds the channel, persist() stores it with its connections
    channel = repository.create({'retry_timeout_milliseconds': 1000})
    listener = channel.add_listener()
    repository.persist(channel)

    # No persist needed: SqliteQueue writes messages itself
    channel.dispatch(listener.id, Message(msg_type='greeting', msg_payload='hello'))
    channel.dispatch(listener.id, Message(msg_type='greeting', msg_payload='are you still there?'))
    print(f'First run: persisted channel {channel.id} and dispatched 2 messages')
    return channel.id, listener.id


async def second_run(db_path: str, channel_id: str, listener_id: str):
    """A new process would start here: everything is loaded from the database."""
    repository = build_repository(db_path)
    channel = repository.load_one(channel_id)
    listener = channel.get_listener(listener_id)
    print(f'Second run: loaded channel with retry timeout {channel.retry_timeout_milliseconds} ms')

    received = 0
    async for event in channel.message_stream(listener):
        print(f'  {event["event"]}: {event["data"]}')
        received += 1
        if received == 2:
            listener.stop()

    # Removes the channel, its connections, listeners and queues identity
    repository.delete(channel_id)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / 'eric.db')
        channel_id, listener_id = first_run(db_path)
        asyncio.run(second_run(db_path, channel_id, listener_id))


if __name__ == '__main__':
    main()
```

Output:

```default
First run: persisted channel 0801e78c-2985-44fd-92f3-6d0a0a20a3d3 and dispatched 2 messages
Second run: loaded channel with retry timeout 1000 ms
  greeting: hello
  greeting: are you still there?
```
