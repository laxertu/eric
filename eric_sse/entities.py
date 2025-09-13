import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any, Iterable

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException, InvalidChannelException
from eric_sse.listener import MessageQueueListener
from eric_sse.connection import Connection, ConnectionsFactory, InMemoryConnectionsFactory
from eric_sse.message import MessageContract, Message
from eric_sse.handlers import ListenerErrorHandler

logger = eric_sse.get_logger()

class _ConnectionManager:
    """Maintains relationships between listeners and connections."""
    def __init__(self, channel_id: str):
        self.__channel_id = channel_id
        self.__listeners: dict[str, MessageQueueListener] = {}
        self.__connections: dict[str, Connection] = {}

    def register_connection(self, connection: Connection):
        self.__connections[connection.listener.id] = connection
        self.__listeners[connection.listener.id] = connection.listener

    def remove_listener(self, listener_id: str):
        try:
            del self.__connections[listener_id]
            del self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException(listener_id) from None

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        try:
            return self.__listeners[listener_id]
        except KeyError:
            raise InvalidListenerException(listener_id) from None

    def get_connection(self, listener_id: str) -> Connection:
        try:
            return self.__connections[listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}") from None

    def get_listeners(self) -> dict[str, MessageQueueListener]:
        """Returns a dict mapping listener ids to listeners"""
        return self.__listeners

    def get_connections(self) -> Iterable[Connection]:
        return self.__connections.values()

class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    :class:`~eric_sse.connection.InMemoryConnectionsFactory` is the default implementation used for **connections_factory** parameter.

    see :class:`~eric_sse.prefabs.SSEChannel`

    :param int stream_delay_seconds: Wait time in seconds between message delivery.
    :param str channel_id: Optionally sets the channel id.
    :param ~eric_sse.connection.ConnectionsFactory connections_factory: Factory to be used for creating connections instances on channel subscriptions.
    """
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

        self.__listeners_error_handlers: list[ListenerErrorHandler] = []



    @property
    def id(self) -> str:
        """Unique identifier for this channel, it can be set by **channel_id** constructor parameter"""
        return self.__id


    @abstractmethod
    def adapt(self, msg: MessageContract) -> Any:
        """Models output of channel streams"""
        ...

    async def message_stream(self, listener: MessageQueueListener) -> AsyncIterable[Any]:
        """
        Entry point for message streaming

        A message with type = 'error' is yield on invalid listener
        """

        # check that listener was registered
        _ = self.__connection_manager.get_listener(listener.id)

        async def new_messages():
            try:
                result = self.deliver_next(listener.id)
                yield result
            except NoMessagesException:
                ...

        async def event_generator() -> AsyncIterable[dict]:

            while True:
                # If client closes connection, stop sending events
                if not listener.is_running():
                    logger.debug("Listener stopped. Exiting")
                    break

                try:
                    async for message in new_messages():
                        yield self.adapt(message)

                    await asyncio.sleep(self.stream_delay_seconds)
                except (InvalidListenerException, InvalidChannelException) as e:
                    yield self.adapt(Message(msg_type='error', msg_payload=e))
                except Exception as e:
                    logger.debug(traceback.format_exc())
                    logger.error(e)
                    yield self.adapt(Message(msg_type='error'))

        async for event in event_generator():
            yield event

    def add_listener(self) -> MessageQueueListener:
        """Shortcut that creates a connection and returns correspondant listener"""
        connection = self.__connections_factory.create()
        self.__connection_manager.register_connection(connection)
        return connection.listener


    def register_listener(self, listener: MessageQueueListener):
        """Registers an existing listener"""
        connection = self.__connections_factory.create(listener=listener)
        self.__connection_manager.register_connection(connection)

    def register_connection(self, connection: Connection):
        """
        Register and existing connection.

        **Warning**: Listener and queue should belong to the same classes returned by connection factory to avoid compatibility issues with persistence layer
        """
        self.__connection_manager.register_connection(connection)

    def register_listener_error_handler(self, handler: ListenerErrorHandler):
        self.__listeners_error_handlers.append(handler)

    def remove_listener(self, listener_id: str):
        self.__connection_manager.remove_listener(listener_id)

    def deliver_next(self, listener_id: str) -> MessageContract:
        """
        Returns next message for given listener id.

        Raises a NoMessagesException if queue is empty
        """
        listener = self.get_listener(listener_id)
        if listener.is_running():
            msg = self._get_connection(listener.id).fetch_message()
            try:
                listener.on_message(msg)
            except Exception as e:
                for handler in self.__listeners_error_handlers:
                    handler.handle_on_message_error(msg=msg, exception=e)
                raise
            return msg

        raise NoMessagesException

    def _get_connection(self, listener_id: str) -> Connection:
        return self.__connection_manager.get_connection(listener_id)

    def dispatch(self, listener_id: str, msg: MessageContract):
        """Adds a message to listener's queue"""

        try:
            self._get_connection(listener_id).send_message(msg)
        except Exception:
            logger.exception("Failed to dispatch message to listener_id=%s", listener_id)
            raise

        logger.debug(f"Dispatched {msg} to {listener_id}")

    def broadcast(self, msg: MessageContract):
        """Enqueue a message to all listeners"""
        for listener_id in self.__connection_manager.get_listeners():
            self.dispatch(listener_id, msg=msg)

    def get_listener(self, listener_id: str) -> MessageQueueListener:
        return self.__connection_manager.get_listener(listener_id)

    def get_connections(self) -> Iterable[Connection]:
        return self.__connection_manager.get_connections()

