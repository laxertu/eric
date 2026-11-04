import asyncio
from concurrent.futures import ThreadPoolExecutor, Executor
from typing import Callable, AsyncIterable
from eric_sse import get_logger
from eric_sse.connection import ConnectionsFactory
from eric_sse.entities import AbstractChannel
from eric_sse.listener import MessageQueueListener
from eric_sse.message import SignedMessage, MessageContract, M, MIn, MOut
from eric_sse.exception import NoMessagesException, InvalidChannelException

logger = get_logger()


def _error_data(exception: Exception) -> dict:
    return {'error': type(exception).__name__, 'message': str(exception)}


class SSEChannel(AbstractChannel[MIn, MOut]):
    """
    SSE streaming channel.
    See `Mozilla docs <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format>`_

    Currently, 'id' field is not supported.
    """

    def __init__(
            self,
            stream_delay_seconds: int = 0,
            retry_timeout_milliseconds: int = 5,
            channel_id: str | None = None,
            connections_factory: ConnectionsFactory | None = None
    ):
        super().__init__(
            stream_delay_seconds=stream_delay_seconds,
            channel_id=channel_id,
            connections_factory=connections_factory
        )
        self.retry_timeout_milliseconds = retry_timeout_milliseconds

    def to_dict(self) -> dict:
        return {**super().to_dict(), 'retry_timeout_milliseconds': self.retry_timeout_milliseconds}

    def adapt(self, msg: MOut) -> dict:
        """
        SSE adapter.

        Returns::

            {
                "event": "message type",
                "retry": "channel time out",
                "data": "original payload",
                "id": "message id"
            }

        "id" is optional, as in SSE specs: it's there only if the message has an :attr:`~eric_sse.message.MessageContract.id`.
        """
        event = {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }
        if msg.id is not None:
            event["id"] = msg.id
        return event

    def adapt_error(self, exception: Exception) -> dict:
        """
        SSE adapter for stream errors.

        Returns::

            {
                "event": "error",
                "retry": "channel time out",
                "data": {"error": "exception class name", "message": "exception message"}
            }
        """
        return {
            "event": "error",
            "retry": self.retry_timeout_milliseconds,
            "data": _error_data(exception)
        }


class DataProcessingChannel(AbstractChannel[MIn, MOut]):
    """
    Channel intended for concurrent processing of data.

    Relies on `concurrent.futures.Executor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor>`_.
    Just override **adapt** method to control output returned to clients
    """

    def __init__(
            self,
            max_workers: int,
            stream_delay_seconds: int = 0,
            executor_class: Executor.__class__ = ThreadPoolExecutor,
            channel_id: str | None = None,
            connections_factory: ConnectionsFactory | None = None
    ):
        """
        :param max_workers: Num of workers to use
        :param stream_delay_seconds: Can be used to limit response rate of streaming. Only applies to message_stream calls.
        :param executor_class: The constructor of some Executor class. Defaults to  `ThreadPoolExecutor  <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`_.
        :param channel_id: Optionally sets the channel id.
        :param connections_factory: See :class:`~eric_sse.entities.AbstractChannel`.
        """
        super().__init__(stream_delay_seconds=stream_delay_seconds, channel_id=channel_id, connections_factory=connections_factory)
        self.max_workers = max_workers
        self.executor_class = executor_class

    def to_dict(self) -> dict:
        """**executor_class** is stored as a class object: the storage engine must be able to serialise it."""
        return {**super().to_dict(), 'max_workers': self.max_workers, 'executor_class': self.executor_class}

    async def process_queue(self, listener: MessageQueueListener[MOut]) -> AsyncIterable[dict]:
        """Performs queue processing of a given listener, returns an AsyncIterable of dictionaries containing message process result. See **adapt** method"""

        with self.executor_class(max_workers=self.max_workers) as e:
            there_are_pending_messages = True
            tasks: list[asyncio.Future[MOut]] = []
            loop = asyncio.get_running_loop()
            while there_are_pending_messages:
                try:
                    msg = self._get_queue(listener_id=listener.id).pop()
                    tasks.append(loop.run_in_executor(e, DataProcessingChannel._invoke_callback_and_return, listener.on_message, msg))

                except NoMessagesException:
                    there_are_pending_messages = False

            for task_dome in asyncio.as_completed(tasks):
                task_result = await task_dome
                yield self.adapt(task_result)

    @staticmethod
    def _invoke_callback_and_return(callback: Callable[[M], None], msg: M) -> M:
        callback(msg)
        return msg

    def adapt(self, msg: MOut) -> dict:
        """

        Returns a dictionary in the following format::

            {
                "event": message type
                "data": message payload
            }
        """

        return {
            "event": msg.type,
            "data": msg.payload
        }

    def adapt_error(self, exception: Exception) -> dict:
        """
        Returns a dictionary in the following format::

            {
                "event": "error",
                "data": {"error": "exception class name", "message": "exception message"}
            }
        """
        return {
            "event": "error",
            "data": _error_data(exception)
        }

class SimpleDistributedApplicationListener(MessageQueueListener[SignedMessage]):
    """
    Listener for distributed applications.

    It dispatches through the channel it is registered to, see :meth:`on_registered`: any channel, including
    when listeners are created or loaded from persistence.
    """

    def __init__(self):
        super().__init__()
        self.__channel: AbstractChannel[SignedMessage, SignedMessage] | None = None
        self.__actions: dict[str, Callable[[SignedMessage], list[MessageContract]]] = dict()
        self.__internal_actions: dict[str, Callable[[], None]] = {
            'start': self.start,
            'stop': self.stop
        }

    def on_registered(self, channel: AbstractChannel[SignedMessage, SignedMessage]) -> None:
        """Keeps **channel**, to dispatch messages through it."""
        self.__channel = channel

    def set_action(self, name: str, action: Callable[[SignedMessage], list[MessageContract]]):
        """
        Hooks a callable to a string key.

        Callables are selected when listener processes the message depending on its type.

        They should return a list of MessageContract instances corresponding to response to action requested.

        Reserved actions are 'start', 'stop'.
        Receiving a message with one of these types will fire corresponding action.

        """
        if name in self.__internal_actions:
            raise KeyError(f'Trying to set an internal action {name}')
        self.__actions[name] = action

    def dispatch_to(self, receiver: MessageQueueListener, msg: MessageContract):
        signed_message = SignedMessage(sender_id=self.id, msg_type=msg.type, msg_payload=msg.payload)
        self.__get_channel().dispatch(receiver.id, signed_message)

    def __get_channel(self) -> AbstractChannel[SignedMessage, SignedMessage]:
        if self.__channel is None:
            raise InvalidChannelException(
                f'Listener {self.id} has no channel: register it to a channel'
            )
        return self.__channel

    def on_message(self, msg: SignedMessage) -> None:
        """Executes action corresponding to message's type"""
        try:
            try:
                self.__internal_actions[msg.type]()
                return
            except KeyError:
                pass

            msgs = self.__actions[msg.type](msg)
            for response in msgs:
                signed_response = SignedMessage(sender_id=self.id, msg_type=response.type, msg_payload=response.payload)
                self.__get_channel().dispatch(msg.sender_id, signed_response)
        except KeyError:
            logger.debug(f'Unknown action {msg.type}')

class SimpleDistributedApplicationChannel(SSEChannel[SignedMessage, SignedMessage]):

    """
    Channel for :class:`~eric_sse.prefabs.SimpleDistributedApplicationListener` instances.

    Use a connections factory or repository that creates them, e.g.
    ``ChannelRepositoryBuilder(SimpleDistributedApplicationChannel).listeners(SimpleDistributedApplicationListener)``.
    """
