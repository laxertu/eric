import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from typing import AsyncIterable, Any, Iterable

import eric_sse
from eric_sse.exception import InvalidListenerException, NoMessagesException, InvalidChannelException, ItemNotFound
from eric_sse.listener import MessageQueueListener
from eric_sse.connection import Connection
from eric_sse.message import MessageContract, Message
from eric_sse.handlers import ListenerErrorHandler
from eric_sse.interfaces import ConnectionRepositoryInterface, KvStorageInterface
from eric_sse.inmemory import InMemoryConnectionRepository

logger = logging.getLogger(__name__)

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
            raise InvalidListenerException(listener_id) from None

    def get_listeners(self) -> dict[str, MessageQueueListener]:
        """Returns a dict mapping listener ids to listeners"""
        return self.__listeners

    def get_connections(self) -> Iterable[Connection]:
        return self.__connections.values()

class AbstractChannel(ABC):
    """
    Base class for channels.

    Provides functionalities for listeners and message delivery management.

    :class:`~eric_sse.inmemory.InMemoryConnectionRepository` is the default implementation used for **connections_repository** parameter.

    see :class:`~eric_sse.prefabs.SSEChannel`

    :param int stream_delay_seconds: Wait time in seconds between message delivery.
    :param str channel_id: Optionally sets the channel id.
    :param ~eric_sse.interfaces.ConnectionRepositoryInterface connections_repository: Factory to be used for creating connections instances on channel subscriptions.
    """
    def __init__(
            self,
            stream_delay_seconds: int = 0,
            channel_id: str | None = None,
            connections_repository: ConnectionRepositoryInterface | None = None,
    ):
        self.__id: str = eric_sse.generate_uuid() if channel_id is None else channel_id
        self.stream_delay_seconds = stream_delay_seconds
        self.__connection_manager: _ConnectionManager = _ConnectionManager(self.__id)
        self.__connections_repository = connections_repository if connections_repository else InMemoryConnectionRepository()

        self.__listeners_error_handlers: list[ListenerErrorHandler] = []



    @property
    def id(self) -> str:
        """Unique identifier for this channel, it can be set by **channel_id** constructor parameter"""
        return self.__id


    @abstractmethod
    def adapt(self, msg: MessageContract) -> Any:
        """Models output of channel streams"""
        ...

    async def message_stream(self, listener_id: str) -> AsyncIterable[Any]:
        """
        Entry point for message streaming

        A message with type = 'error' is yield on invalid listener
        """
        listener = self.get_listener(listener_id)

        async def new_messages():
            try:
                result = self.deliver_next(listener_id)
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
        connection = self.__connections_repository.connections_factory.create()
        self.__connection_manager.register_connection(connection)
        return connection.listener


    def register_listener(self, listener: MessageQueueListener):
        """Registers an existing listener"""
        connection = self.__connections_repository.connections_factory.create(listener=listener)
        self.__connection_manager.register_connection(connection)

    def register_connection(self, connection: Connection):
        """
        Register an existing connection.

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


class ChannelRepositoryInterface(ABC):

    @property
    @abstractmethod
    def connections_repository(self) -> ConnectionRepositoryInterface:
        """Repository to be used to persist connections."""
        pass

    @abstractmethod
    def load_all(self) -> Iterable[AbstractChannel]:
        """Loads all channels"""
        pass

    @abstractmethod
    def load_one(self, channel_id: str) -> AbstractChannel:
        """Loads a channel given its it"""
        pass

    @abstractmethod
    def persist(self, channel: AbstractChannel):
        """Persists a channel"""
        pass

    @abstractmethod
    def delete(self, channel_id: str):
        """Deletes a channel given its it"""
        pass

    @abstractmethod
    def create(self, channel_data: dict) -> AbstractChannel:
        """Creates a new channel and configures it depending on channel_data."""
        pass


class AbstractChannelRepository(ChannelRepositoryInterface, ABC):
    """
    Abstract base class for channel repositories.

    Builds channels before return them using injected repositories
    """
    def __init__(
            self,
            storage: KvStorageInterface,
            connections_repository: ConnectionRepositoryInterface
    ):
        self.__storage = storage
        self.__connections_repository = connections_repository

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connections_repository


    @staticmethod
    @abstractmethod
    def _channel_to_dict(channel: AbstractChannel) -> dict:
        """
        Returns a dictionary representation of the channel to be passed to :meth:`eric_sse.interfaces.ChannelRepositoryInterface.create` calls.
        """
        pass

    def _setup_channel(self, channel: AbstractChannel):
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            channel.register_connection(connection)
        return channel

    def load_all(self) -> Iterable[AbstractChannel]:
        for channel_data in self.__storage.fetch_all():
            channel = self.create(channel_data)
            for connection in self.__connections_repository.load_all(channel_id=channel.id):
                channel.register_connection(connection)
            yield channel

    def load_one(self, channel_id: str) -> AbstractChannel:
        channel = self.create(self.__storage.fetch_one(channel_id))
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            channel.register_connection(connection)
        return channel

    def persist(self, channel: AbstractChannel):
        self.__storage.upsert(channel.id, self._channel_to_dict(channel))

        persisted_connections_ids = {c.id for c in self.__connections_repository.load_all(channel_id=channel.id)}
        current_connections_ids = set()

        for connection in channel.get_connections():
            current_connections_ids.add(connection.id)
            self.__connections_repository.persist(channel_id=channel.id, connection=connection)

        for connection_id_to_remove in persisted_connections_ids - current_connections_ids:
            self.__connections_repository.delete(connection_id=connection_id_to_remove)

    def delete(self, channel_id: str):
        try:
            channel = self.load_one(channel_id)
        except ItemNotFound:
            return
        for connection in self.__connections_repository.load_all(channel_id=channel.id):
            self.__connections_repository.delete(connection_id=connection.id)
        self.__storage.delete(channel_id)
