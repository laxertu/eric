import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any, Iterable, TypeVar, Generic

import eric_sse
from eric_sse.exception import InvalidConnectionException, NoMessagesException, InvalidChannelException, \
    InternalStreamError, StoppedListenerException
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.connection import Connection, ConnectionsFactory, InMemoryConnectionsFactory
from eric_sse.message import MIn, MOut
from eric_sse.queues import Queue

logger = eric_sse.get_logger()

_Channel = TypeVar('_Channel', bound='AbstractChannel')

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_eof'
MESSAGE_TYPE_INTERNAL_ERROR = '_eric_error'


class _ConnectionManager(Generic[MIn, MOut]):
    """Keeps the connections of a channel, by connection id"""
    def __init__(self, channel_id: str):
        self.__channel_id = channel_id
        self.__connections: dict[str, Connection[MessageQueueListener[MOut], Queue[MIn, MOut]]] = {}

    def register_connection(self, connection: Connection):
        self.__connections[connection.id] = connection

    def remove_connection(self, connection_id: str):
        try:
            del self.__connections[connection_id]
        except KeyError:
            raise InvalidConnectionException(connection_id) from None

    def get_connection(self, connection_id: str) -> Connection[MessageQueueListener[MOut], Queue[MIn, MOut]]:
        try:
            return self.__connections[connection_id]
        except KeyError:
            raise InvalidConnectionException(f"Invalid connection {connection_id}") from None

    def get_connections(self) -> Iterable[Connection]:
        return self.__connections.values()

class AbstractChannel(ABC, Generic[MIn, MOut]):
    """
    Base class for channels.

    Provides functionalities for connections and message delivery management. A connection pairs a listener with its
    queue, and its id is the address messages are dispatched to, see :class:`~eric_sse.connection.Connection`.

    Generic on the type of messages it dispatches (**MIn**) and delivers (**MOut**), e.g.
    ``SSEChannel[SignedMessage, SignedMessage]``, as its queues are ``Queue[MIn, MOut]`` and its listeners
    ``MessageQueueListener[MOut]``. They differ when queues transform messages, e.g.
    ``SSEChannel[MessageContract, ReliableMessage]`` with :class:`~eric_sse.queue_patterns.ReliableQueue` queues.
    Plain channels handle any message.

    :class:`~eric_sse.connection.InMemoryConnectionsFactory` is the default implementation used for **connections_factory** parameter.

    see :class:`~eric_sse.prefabs.SSEChannel`

    **Hooks**: subclasses can override :meth:`on_connection_added`, :meth:`on_connection_removed`,
    :meth:`on_stream_start`, :meth:`on_stream_end`, :meth:`on_wait_timeout`, :meth:`before_dispatch` and :meth:`on_error`.
    They do nothing by default.

    **Error handlers**: errors raised by queues and listeners are passed to the handlers registered with
    :meth:`add_queuing_error_handler` and :meth:`add_listener_error_handler`.
    Then they are either re-raised or, when the channel swallows them, logged.
    Control flow exceptions, like :class:`~eric_sse.exception.NoMessagesException`, are neither logged nor handled.

    :param int stream_delay_seconds: Pause in seconds after each message delivered by :meth:`message_stream`. Can be used to limit its rate.
    :param str channel_id: Optionally sets the channel id.
    :param ~eric_sse.connection.ConnectionsFactory connections_factory: Factory to be used for creating connections instances on channel subscriptions.
    """
    wait_timeout_seconds: float = 1.0
    """How long :meth:`message_stream` waits for a message before checking again whether its listener is running."""

    def __init__(
            self,
            stream_delay_seconds: int = 0,
            channel_id: str | None = None,
            connections_factory: ConnectionsFactory | None = None,
    ):
        self.__id: str = eric_sse.generate_uuid() if channel_id is None else channel_id
        self.stream_delay_seconds = stream_delay_seconds
        self.__connection_manager: _ConnectionManager = _ConnectionManager(self.__id)
        self.__connections_factory = connections_factory if connections_factory else InMemoryConnectionsFactory()
        self.__queuing_error_handlers: list[QueuingErrorHandler] = []
        self.__listener_error_handlers: list[ListenerErrorHandler] = []

    def add_queuing_error_handler(self, handler: QueuingErrorHandler) -> None:
        """Registers a handler for errors raised by queues. Handlers are called in registration order, and are not persisted."""
        self.__queuing_error_handlers.append(handler)

    def add_listener_error_handler(self, handler: ListenerErrorHandler) -> None:
        """Registers a handler for errors raised by listeners. Handlers are called in registration order, and are not persisted."""
        self.__listener_error_handlers.append(handler)

    @staticmethod
    def __log_error(exception: Exception) -> None:
        logger.debug(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
        logger.error(exception)

    def __on_pop_error(self, connection_id: str, exception: Exception) -> None:
        for handler in self.__queuing_error_handlers:
            handler.handle_pop_error(connection_id, exception)

    def __notify_listener(self, connection: Connection, msg: MOut) -> None:
        try:
            connection.listener.on_message(msg)
        except Exception as e:
            self._on_listener_error(connection.id, msg, e)

    def __running_connection(self, connection_id: str) -> Connection:
        connection = self.get_connection(connection_id)
        if not connection.listener.is_running():
            raise StoppedListenerException(connection_id)
        return connection

    def _pop_next(self, connection_id: str) -> MOut:
        """
        Pops the next message of given connection, without notifying its listener: the first half of
        :meth:`deliver_next`, for subclasses that notify listeners their own way, e.g. in an executor.
        Then they must pass listener errors to :meth:`_on_listener_error`.

        Raises as :meth:`deliver_next` does. Queue errors are re-raised after error handlers.
        """
        connection = self.__running_connection(connection_id)
        try:
            return connection.queue.pop()
        except NoMessagesException:
            raise
        except Exception as e:
            self.__on_pop_error(connection_id, e)
            raise

    def _on_listener_error(self, connection_id: str, msg: MOut, exception: Exception) -> None:
        """Logs an error raised by a listener's ``on_message``, and passes it to error handlers."""
        self.__log_error(exception)
        for handler in self.__listener_error_handlers:
            handler.handle_on_message_error(connection_id, msg, exception)


    @property
    def id(self) -> str:
        """Unique identifier for this channel, it can be set by **channel_id** constructor parameter"""
        return self.__id

    def to_dict(self) -> dict:
        """
        Channel configuration to be persisted. Keys must be constructor parameters, see :meth:`from_dict`.

        Subclasses with additional configuration should extend it::

            def to_dict(self) -> dict:
                return {**super().to_dict(), 'my_param': self.my_param}
        """
        return {
            'channel_id': self.id,
            'stream_delay_seconds': self.stream_delay_seconds,
        }

    @classmethod
    def from_dict(cls: type[_Channel], data: dict, connections_factory: ConnectionsFactory | None = None) -> _Channel:
        """
        Builds a channel from a :meth:`to_dict` representation. Override it if constructor parameters don't match **data** keys.

        :param data: Constructor parameters, except **connections_factory**.
        :param ~eric_sse.connection.ConnectionsFactory connections_factory:
        """
        return cls(**data, connections_factory=connections_factory)


    @abstractmethod
    def adapt(self, msg: MOut) -> Any:
        """Models output of channel streams"""
        ...

    @abstractmethod
    def adapt_error(self, exception: Exception) -> Any:
        """
        Models errors in channel streams, see :meth:`message_stream`.

        **exception** is safe to expose to clients: unexpected errors are replaced by an
        :class:`~eric_sse.exception.InternalStreamError`, that hides their details.
        """
        ...

    def on_connection_added(self, connection: Connection) -> None:
        """
        Hook called by :meth:`add_connection` and :meth:`register_listener`.

        Not called when connections are registered with :meth:`register_connection`, e.g. when a channel is
        loaded from persistence, because that's not a new subscription.
        """
        pass

    def on_connection_removed(self, connection: Connection) -> None:
        """Hook called by :meth:`remove_connection`, after the connection has been removed."""
        pass

    def on_stream_start(self, connection: Connection) -> None:
        """Hook called when :meth:`message_stream` starts, after the listener has been started."""
        pass

    def on_stream_end(self, connection: Connection) -> None:
        """Hook called when :meth:`message_stream` ends, for any reason: listener stopped, error, or client disconnection."""
        pass

    def before_dispatch(self, connection_id: str, msg: MIn) -> MIn | None:
        """
        Hook called by :meth:`dispatch`, and so by :meth:`broadcast` for each connection, before enqueuing **msg**.

        :return: The message to enqueue, possibly a different one, or None to drop it.
        """
        return msg

    def on_wait_timeout(self, connection: Connection) -> None:
        """
        Hook called when :meth:`message_stream` waited :attr:`wait_timeout_seconds` for a message and none arrived.

        It is not an error: an idle stream times out periodically, to check whether its listener is still running.
        Can be used, for example, to collect metrics or to end idle streams by stopping their listener.
        """
        pass

    def on_error(self, connection: Connection, exception: Exception) -> bool:
        """
        Hook called when :meth:`message_stream` catches an unexpected exception, before yielding an error.

        By default, it goes on. The exception has already been logged, and, if raised by a queue, passed to error handlers.
        The stream waits :attr:`wait_timeout_seconds` before trying again, so a failing backend doesn't make it spin.

        :return: False to end the stream after the error.
        """
        return True

    async def message_stream(self, connection_id: str) -> AsyncIterable[Any]:
        """
        Entry point for message streaming. Starts the connection's listener, and ends when it is stopped.

        Waits for messages through :meth:`wait_next`, so an idle stream doesn't consume CPU.
        A stopped listener is noticed at the latest after :attr:`wait_timeout_seconds`.

        Errors are yielded through :meth:`adapt_error`. After an invalid listener or channel error, or a :class:`~eric_sse.exception.StoppedListenerException`, the stream ends.
        Unexpected errors are logged and yielded as an :class:`~eric_sse.exception.InternalStreamError`, hiding
        their details, and :meth:`on_error` decides whether the stream goes on.

        Calls :meth:`on_stream_start`, :meth:`on_wait_timeout` and :meth:`on_stream_end` hooks.
        """
        connection = self.get_connection(connection_id)
        listener = connection.listener
        listener.start()
        self.on_stream_start(connection)

        try:
            while listener.is_running():
                try:
                    try:
                        message = await self.wait_next(connection_id, self.wait_timeout_seconds)
                    except NoMessagesException:
                        self.on_wait_timeout(connection)
                        continue

                    yield self.adapt(message)

                    if self.stream_delay_seconds > 0:
                        await asyncio.sleep(self.stream_delay_seconds)
                except (InvalidConnectionException, InvalidChannelException, StoppedListenerException) as e:
                    yield self.adapt_error(e)
                    break
                except Exception as e:
                    self.__log_error(e)
                    go_on = self.on_error(connection, e)
                    yield self.adapt_error(InternalStreamError())
                    if not go_on:
                        break
                    await asyncio.sleep(self.wait_timeout_seconds)
        finally:
            logger.debug("Stream ended")
            self.on_stream_end(connection)

    def add_connection(self) -> Connection:
        """Creates a connection through the connections factory, and registers it."""
        connection = self.__connections_factory.create()
        self.register_connection(connection)
        self.on_connection_added(connection)
        return connection

    def register_listener(self, listener: MessageQueueListener[MOut]) -> Connection:
        """Creates a connection for an existing listener, and registers it."""
        connection = self.__connections_factory.create(listener=listener)
        self.register_connection(connection)
        self.on_connection_added(connection)
        return connection

    def register_connection(self, connection: Connection):
        """
        Register and existing connection. :meth:`add_connection` and :meth:`register_listener` call it too,
        so subclasses can override it to set up every new connection.

        Calls :meth:`~eric_sse.listener.MessageQueueListener.on_registered` on the connection's listener.

        **Warning**: Listener and queue should belong to the same classes created by the connections factory (the connections repository, for channels built by a channel repository) to avoid compatibility issues with persistence layer
        """
        self.__connection_manager.register_connection(connection)
        connection.listener.on_registered(self, connection.id)

    def remove_connection(self, connection_id: str):
        connection = self.get_connection(connection_id)
        self.__connection_manager.remove_connection(connection_id)
        self.on_connection_removed(connection)

    def deliver_next(self, connection_id: str) -> MOut:
        """
        Returns next message of given connection.

        Raises a :class:`~eric_sse.exception.StoppedListenerException` if the listener is not running, even if its
        queue is empty, and a NoMessagesException if the queue is empty.
        Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.
        """
        msg = self._pop_next(connection_id)
        self.__notify_listener(self.get_connection(connection_id), msg)
        return msg

    async def wait_next(self, connection_id: str, timeout: float) -> MOut:
        """
        Waits up to **timeout** seconds for the next message of given connection, without blocking the event loop.

        Raises a :class:`~eric_sse.exception.StoppedListenerException` if the listener is not running, as waiting for
        messages that it won't receive is not allowed, and a NoMessagesException if no message arrives in time.
        Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.
        """
        connection = self.__running_connection(connection_id)
        try:
            msg = await connection.queue.wait_pop(timeout)
        except NoMessagesException:
            raise
        except Exception as e:
            self.__on_pop_error(connection_id, e)
            raise
        self.__notify_listener(connection, msg)
        return msg

    def dispatch(self, connection_id: str, msg: MIn):
        """
        Adds a message to the connection's queue, unless :meth:`before_dispatch` drops it.

        Queue errors are re-raised after error handlers.
        """
        push_error = self.__dispatch(self.get_connection(connection_id), msg)
        if push_error is not None:
            raise push_error

    def __dispatch(self, connection: Connection, msg: MIn) -> Exception | None:
        """Returns the push error, if any, after passing it to error handlers."""
        to_push = self.before_dispatch(connection.id, msg)
        if to_push is None:
            logger.debug(f"Message dropped for {connection.id}")
            return None
        try:
            connection.queue.push(to_push)
        except Exception as e:
            for handler in self.__queuing_error_handlers:
                handler.handle_push_error(connection.id, to_push, e)
            return e
        logger.debug(f"Dispatched {to_push} to {connection.id}")
        return None

    def broadcast(self, msg: MIn):
        """
        Enqueue a message to the connections registered when it starts. A queue error is logged, and doesn't stop
        delivery to the other ones. Hooks and error handlers can remove connections meanwhile.
        """
        for connection in list(self.__connection_manager.get_connections()):
            push_error = self.__dispatch(connection, msg=msg)
            if push_error is not None:
                self.__log_error(push_error)

    def get_connection(self, connection_id: str) -> Connection:
        """Raises an :class:`~eric_sse.exception.InvalidConnectionException` if the channel has no such connection."""
        return self.__connection_manager.get_connection(connection_id)

    def get_connections(self) -> Iterable[Connection]:
        return self.__connection_manager.get_connections()

    async def watch(self) -> AsyncIterable[Any]:
        """
        Streams channel messages through a new connection, removed when the stream ends::

            async for message in channel.watch():
                ...
        """
        connection = self.add_connection()
        try:
            async for message in self.message_stream(connection.id):
                yield message
        finally:
            try:
                self.remove_connection(connection.id)
            except InvalidConnectionException:
                pass

