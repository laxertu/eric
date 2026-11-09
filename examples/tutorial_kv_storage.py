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
        ChannelRepositoryBuilder(SSEChannel, SqliteStorage(db_path))
        .queues(queue_factory=lambda: SqliteQueue(db_path))
        .build()
    )


def first_run(db_path: str) -> tuple[str, str]:
    """Creates and persists a channel with one connection, then dispatches messages."""
    repository = build_repository(db_path)

    # Nothing is persisted implicitly: create() only builds the channel, persist() stores it with its connections
    channel = repository.create({'retry_timeout_milliseconds': 1000})
    connection = channel.add_connection()
    repository.persist(channel)

    # No persist needed: SqliteQueue writes messages itself
    channel.dispatch(connection.id, Message(msg_type='greeting', msg_payload='hello'))
    channel.dispatch(connection.id, Message(msg_type='greeting', msg_payload='are you still there?'))
    print(f'First run: persisted channel {channel.id} and dispatched 2 messages')
    return channel.id, connection.id


async def second_run(db_path: str, channel_id: str, connection_id: str):
    """A new process would start here: everything is loaded from the database."""
    repository = build_repository(db_path)
    channel = repository.load_one(channel_id)
    listener = channel.get_connection(connection_id).listener
    print(f'Second run: loaded channel with retry timeout {channel.retry_timeout_milliseconds} ms')

    received = 0
    async for event in channel.message_stream(connection_id):
        print(f'  {event["event"]}: {event["data"]}')
        received += 1
        if received == 2:
            listener.stop()

    # Removes the channel, its connections, listeners and queues identity
    repository.delete(channel_id)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / 'eric.db')
        channel_id, connection_id = first_run(db_path)
        asyncio.run(second_run(db_path, channel_id, connection_id))


if __name__ == '__main__':
    main()
