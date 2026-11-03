import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any, Iterable, TypeVar, Generic

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException, InvalidChannelException, \
    InternalStreamError
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.listener import MessageQueueListener
from eric_sse.connection import Connection, ConnectionsFactory, InMemoryConnectionsFactory
from eric_sse.message import M
from eric_sse.queues import Queue

logger = eric_sse.get_logger()

_Channel = TypeVar('_Channel', bound='AbstractChannel')

MESSAGE_TYPE_CLOSED = '_eric_channel_closed'
MESSAGE_TYPE_END_OF_STREAM = '_eric_channel_eof'
MESSAGE_TYPE_INTERNAL_ERROR = '_eric_error'


class _ConnectionManager(Generic[M]):
    """Maintains relationships between listeners and queues"""
    def __init__(self, channel_id: str):
        self.__channel_id = channel_id
        self.__listeners: dict[str, MessageQueueListener[M]] = {}
        self.__queues: dict[str, Queue[M]] = {}
        self.__connections: dict[str, Connection] = {}

    def register_connection(self, connection: Connection):
        self.__connections[connection.listener.id] = connection
        self.__queues[connection.listener.id] = connection.queue
        self.__listeners[connection.listener.id] = connection.listener

    def remove_listener(self, listener_id: str):
        try:
            del self.__connections[listener_id]
            del self.__queues[listener_id]
            del self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException(listener_id) from None

    def get_queue(self, listener_id: str) -> Queue[M]:
        try:
            return self.__queues[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}") from None

    def get_listener(self, listener_id: str) -> MessageQueueListener[M]:
        try:
            return self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException

    def get_listeners(self) -> dict[str, MessageQueueListener[M]]:
        """Returns a dict mapping listener ids to listeners"""
        return self.__listeners

    def get_connections(self) -> Iterable[Connection]:
        return self.__connections.values()

class AbstractChannel(ABC, Generic[M]):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    Generic on the type of messages it dispatches and delivers, e.g. ``SSEChannel[SignedMessage]``, and so on the
    type of its listeners and queues. Plain channels handle any message.

    :class:`~eric_sse.connection.InMemoryConnectionsFactory` is the default implementation used for **connections_factory** parameter.

    see :class:`~eric_sse.prefabs.SSEChannel`

    **Hooks**: subclasses can override :meth:`on_listener_added`, :meth:`on_listener_removed`,
    :meth:`on_stream_start`, :meth:`on_stream_end`, :meth:`before_dispatch` and :meth:`on_error`.
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

    def __on_pop_error(self, listener_id: str, exception: Exception) -> None:
        for handler in self.__queuing_error_handlers:
            handler.handle_pop_error(listener_id, exception)

    def __notify_listener(self, listener: MessageQueueListener[M], msg: M) -> None:
        try:
            listener.on_message(msg)
        except Exception as e:
            self.__log_error(e)
            for handler in self.__listener_error_handlers:
                handler.handle_on_message_error(listener.id, msg, e)


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
    def adapt(self, msg: M) -> Any:
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

    def on_listener_added(self, listener: MessageQueueListener[M]) -> None:
        """
        Hook called by :meth:`add_listener` and :meth:`register_listener`.

        Not called when connections are registered with :meth:`register_connection`, e.g. when a channel is
        loaded from persistence, because that's not a new subscription.
        """
        pass

    def on_listener_removed(self, listener: MessageQueueListener[M]) -> None:
        """Hook called by :meth:`remove_listener`, after the listener has been removed."""
        pass

    def on_stream_start(self, listener: MessageQueueListener[M]) -> None:
        """Hook called when :meth:`message_stream` starts, after the listener has been started."""
        pass

    def on_stream_end(self, listener: MessageQueueListener[M]) -> None:
        """Hook called when :meth:`message_stream` ends, for any reason: listener stopped, error, or client disconnection."""
        pass

    def before_dispatch(self, listener_id: str, msg: M) -> M | None:
        """
        Hook called by :meth:`dispatch`, and so by :meth:`broadcast` for each listener, before enqueuing **msg**.

        :return: The message to enqueue, possibly a different one, or None to drop it.
        """
        return msg

    def on_error(self, listener: MessageQueueListener[M], exception: Exception) -> bool:
        """
        Hook called when :meth:`message_stream` catches an unexpected exception, before yielding an error.

        By default it goes on. The exception has already been logged, and, if raised by a queue, passed to error handlers.
        The stream waits :attr:`wait_timeout_seconds` before trying again, so a failing backend doesn't make it spin.

        :return: False to end the stream after the error.
        """
        return True

    async def message_stream(self, listener: MessageQueueListener[M]) -> AsyncIterable[Any]:
        """
        Entry point for message streaming. Starts **listener**, and ends when it is stopped.

        Waits for messages through :meth:`wait_next`, so an idle stream doesn't consume CPU.
        A stopped listener is noticed at the latest after :attr:`wait_timeout_seconds`.

        Errors are yielded through :meth:`adapt_error`. After an invalid listener or channel error the stream ends.
        Unexpected errors are logged and yielded as an :class:`~eric_sse.exception.InternalStreamError`, hiding
        their details, and :meth:`on_error` decides whether the stream goes on.

        Calls :meth:`on_stream_start` and :meth:`on_stream_end` hooks.
        """
        self.__connection_manager.get_listener(listener.id)
        listener.start()
        self.on_stream_start(listener)

        try:
            while listener.is_running():
                try:
                    try:
                        message = await self.wait_next(listener.id, self.wait_timeout_seconds)
                    except NoMessagesException:
                        continue

                    yield self.adapt(message)

                    if self.stream_delay_seconds > 0:
                        await asyncio.sleep(self.stream_delay_seconds)
                except (InvalidListenerException, InvalidChannelException) as e:
                    yield self.adapt_error(e)
                    break
                except Exception as e:
                    self.__log_error(e)
                    go_on = self.on_error(listener, e)
                    yield self.adapt_error(InternalStreamError())
                    if not go_on:
                        break
                    await asyncio.sleep(self.wait_timeout_seconds)
        finally:
            logger.debug("Stream ended")
            self.on_stream_end(listener)

    def add_listener(self) -> MessageQueueListener[M]:
        """Shortcut that creates a connection and returns correspondant listener"""
        connection = self.__connections_factory.create()
        self.register_connection(connection)
        self.on_listener_added(connection.listener)
        return connection.listener


    def register_listener(self, listener: MessageQueueListener[M]):
        """Registers an existing listener"""
        connection = self.__connections_factory.create(listener=listener)
        self.register_connection(connection)
        self.on_listener_added(connection.listener)

    def register_connection(self, connection: Connection):
        """
        Register and existing connection. :meth:`add_listener` and :meth:`register_listener` call it too,
        so subclasses can override it to set up every new connection.

        **Warning**: Listener and queue should belong to the same classes created by the connections factory (the connections repository, for channels built by a channel repository) to avoid compatibility issues with persistence layer
        """
        self.__connection_manager.register_connection(connection)

    def remove_listener(self, listener_id: str):
        listener = self.__connection_manager.get_listener(listener_id)
        self.__connection_manager.remove_listener(listener_id)
        self.on_listener_removed(listener)

    def deliver_next(self, listener_id: str) -> M:
        """
        Returns next message for given listener id.

        Raises a NoMessagesException if queue is empty.
        Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.
        """
        listener = self.get_listener(listener_id)
        if listener.is_running():
            queue = self.__connection_manager.get_queue(listener.id)
            try:
                msg = queue.pop()
            except NoMessagesException:
                raise
            except Exception as e:
                self.__on_pop_error(listener.id, e)
                raise
            self.__notify_listener(listener, msg)
            return msg

        raise NoMessagesException

    async def wait_next(self, listener_id: str, timeout: float) -> M:
        """
        Waits up to **timeout** seconds for the next message for given listener id, without blocking the event loop.

        Raises a NoMessagesException if the listener is not running or no message arrives in time.
        Queue errors are re-raised after error handlers; listener errors are not, and the message is returned anyway.
        """
        listener = self.get_listener(listener_id)
        if not listener.is_running():
            raise NoMessagesException

        try:
            msg = await self._get_queue(listener.id).wait_pop(timeout)
        except NoMessagesException:
            raise
        except Exception as e:
            self.__on_pop_error(listener.id, e)
            raise
        self.__notify_listener(listener, msg)
        return msg

    def _get_queue(self, listener_id: str) -> Queue[M]:
        return self.__connection_manager.get_queue(listener_id)

    def dispatch(self, listener_id: str, msg: M):
        """
        Adds a message to listener's queue, unless :meth:`before_dispatch` drops it.

        Queue errors are re-raised after error handlers.
        """
        push_error = self.__dispatch(listener_id, msg)
        if push_error is not None:
            raise push_error

    def __dispatch(self, listener_id: str, msg: M) -> Exception | None:
        """Returns the push error, if any, after passing it to error handlers."""
        queue = self._get_queue(listener_id)
        to_push = self.before_dispatch(listener_id, msg)
        if to_push is None:
            logger.debug(f"Message dropped for {listener_id}")
            return None
        try:
            queue.push(to_push)
        except Exception as e:
            for handler in self.__queuing_error_handlers:
                handler.handle_push_error(listener_id, to_push, e)
            return e
        logger.debug(f"Dispatched {to_push} to {listener_id}")
        return None

    def broadcast(self, msg: M):
        """Enqueue a message to all listeners. A queue error is logged, and doesn't stop delivery to the other ones."""
        for listener_id in self.__connection_manager.get_listeners():
            push_error = self.__dispatch(listener_id, msg=msg)
            if push_error is not None:
                self.__log_error(push_error)

    def get_listener(self, listener_id: str) -> MessageQueueListener[M]:
        return self.__connection_manager.get_listener(listener_id)

    def get_connections(self) -> Iterable[Connection]:
        return self.__connection_manager.get_connections()

    async def watch(self) -> AsyncIterable[Any]:
        """
        Streams channel messages through a new listener, removed when the stream ends::

            async for message in channel.watch():
                ...
        """
        listener = self.add_listener()
        try:
            async for message in self.message_stream(listener):
                yield message
        finally:
            try:
                self.remove_listener(listener.id)
            except InvalidListenerException:
                pass

