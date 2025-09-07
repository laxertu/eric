import asyncio
from concurrent.futures import ThreadPoolExecutor, Executor
from typing import Callable, AsyncIterable
from eric_sse import get_logger
from eric_sse.connection import ConnectionsFactory
from eric_sse.entities import AbstractChannel
from eric_sse.listener import MessageQueueListener
from eric_sse.message import SignedMessage, MessageContract
from eric_sse.exception import NoMessagesException
from eric_sse.repository import AbstractChannelRepository

logger = get_logger()


class SSEChannel(AbstractChannel):
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

    def adapt(self, msg: MessageContract) -> dict:
        """
        SSE adapter.

        Returns::

            {
                "event": "message type",
                "retry": "channel time out",
                "data": "original payload"
            }
        """
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }


class DataProcessingChannel(AbstractChannel):
    """
    Channel intended for concurrent processing of data.

    Relies on `concurrent.futures.Executor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor>`_.
    Just override **adapt** method to control output returned to clients
    """

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0, executor_class: Executor.__class__ = ThreadPoolExecutor):
        """
        :param max_workers: Num of workers to use
        :param stream_delay_seconds: Can be used to limit response rate of streaming. Only applies to message_stream calls.
        :param executor_class: The constructor of some Executor class. Defaults to  `ThreadPoolExecutor  <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`_.
        """
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.max_workers = max_workers
        self.executor_class = executor_class

    async def process_queue(self, listener: MessageQueueListener) -> AsyncIterable[dict]:
        """Performs queue processing of a given listener, returns an AsyncIterable of dictionaries containing message process result. See **adapt** method"""

        with self.executor_class(max_workers=self.max_workers) as e:
            there_are_pending_messages = True
            tasks = []
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
    def _invoke_callback_and_return(callback: Callable[[MessageContract], None], msg: MessageContract):
        callback(msg)
        return msg

    def adapt(self, msg: MessageContract) -> dict:
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

class SimpleDistributedApplicationListener(MessageQueueListener):
    """Listener for distributed applications"""

    def __init__(self):
        super().__init__()
        self.__channel: AbstractChannel | None = None
        self.__actions: dict[str, Callable[[MessageContract], list[MessageContract]]] = dict()
        self.__internal_actions: dict[str, Callable[[], None]] = {
            'start': self.start,
            'stop': self.stop
        }

    def set_channel(self, channel: AbstractChannel):
        self.__channel = channel

    def set_action(self, name: str, action: Callable[[MessageContract], list[MessageContract]]):
        """
        Hooks a callable to a string key.

        Callables are selected when listener processes the message depending on its type.

        They should return a list of MessageContract instances corresponding to response to action requested.

        Reserved actions are 'start', 'stop'.
        Receiving a message with one of these types will fire corresponding action.

        """
        if action in self.__internal_actions:
            raise KeyError(f'Trying to set an internal action {action}')
        self.__actions[name] = action

    def dispatch_to(self, receiver: MessageQueueListener, msg: MessageContract):
        signed_message = SignedMessage(sender_id=self.id, msg_type=msg.type, msg_payload=msg.payload)
        self.__channel.dispatch(receiver.id, signed_message)

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
                self.__channel.dispatch(msg.sender_id, signed_response)
        except KeyError:
            logger.debug(f'Unknown action {msg.type}')

class SimpleDistributedApplicationChannel(SSEChannel):

    def register_listener(self, listener: SimpleDistributedApplicationListener):
        listener.set_channel(self)
        super().register_listener(listener=listener)


class SSEChannelRepository(AbstractChannelRepository):
    """
    Enable SSE channels persistence
    """
    def create(self, channel_data: dict) -> SSEChannel:
        """
        :param dict channel_data: Fill it with SSEChannel constructor arguments, except for connections_factory that wil be injected by repository
        """
        return SSEChannel(**channel_data, connections_factory=self.connections_factory)

    @staticmethod
    def _channel_to_dict(channel: SSEChannel) -> dict:
        """
        Returns a dictionary representation of the SSE channel to be passed to create() calls.
        """
        return {
            'retry_timeout_milliseconds': channel.retry_timeout_milliseconds,
            'stream_delay_seconds': channel.stream_delay_seconds,
            'channel_id': channel.id,
        }
