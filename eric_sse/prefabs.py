from asyncio import create_task, gather
from concurrent.futures import ThreadPoolExecutor, Executor
from typing import Callable, AsyncIterable
from eric_sse import get_logger
from eric_sse.entities import AbstractChannel
from eric_sse.listener import MessageQueueListener
from eric_sse.message import SignedMessage, MessageContract
from eric_sse.exception import NoMessagesException
from eric_sse.repository import AbstractMessageQueueRepository

logger = get_logger()


class SSEChannel(AbstractChannel):
    """
    SSE streaming channel.
    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format

    Currently, 'id' field is not supported.

    :param int stream_delay_seconds:
    :param int retry_timeout_milliseconds:
    :param eric_sse.repository.AbstractMessageQueueRepository queues_repository:
    """

    def __init__(
            self,
            stream_delay_seconds: int = 0,
            retry_timeout_milliseconds: int = 5,
            queues_repository: AbstractMessageQueueRepository = None
    ):
        super().__init__(stream_delay_seconds=stream_delay_seconds, queues_repository=queues_repository)
        self.retry_timeout_milliseconds = retry_timeout_milliseconds

        self.payload_adapter: (
            Callable)[[dict | list | str | int | float | None], dict | list | str | int | float | None] = lambda x: x
        """Message payload adapter, defaults to identity (leave as is). It can be used, for example, when working in a 
        context where receiver is responsible for payload deserialization, e.g. Sockets"""

    def adapt(self, msg: MessageContract) -> dict:
        """
        SSE adapter.

        Returns::

            {
                "event": "message type",
                "retry": "channel time out",
                "data": "original payload (by default)"
            }
        """
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": self.payload_adapter(msg.payload)
        }


class DataProcessingChannel(AbstractChannel):
    """
    Channel intended for concurrent processing of data.

    Relies on `concurrent.futures.ThreadPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor>`_.
    Just override **adapt** method to control output returned to clients

    MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.  
    """

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0, executor_class: Executor.__class__ = ThreadPoolExecutor):
        """
        :param max_workers: Num of workers to use
        :param stream_delay_seconds: Can be used to limit response rate of streaming. Only applies to message_stream calls.
        """
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.max_workers = max_workers
        self.executor_class = executor_class

    async def process_queue(self, listener: MessageQueueListener) -> AsyncIterable[dict]:
        """Starts a process by creating self.max_workers workers and executing on_message method of listener in parallel."""

        with self.executor_class(max_workers=self.max_workers) as e:
            there_are_pending_messages = True
            tasks = []

            while there_are_pending_messages:
                try:
                    msg = await self._get_queue(listener_id=listener.id).pop()
                    tasks.append(create_task(self._invoke_callback_and_return(callback=listener.on_message, msg=msg)))

                except NoMessagesException:
                    there_are_pending_messages = False

            for processed_message in await gather(*tasks):
                yield self.adapt(processed_message)


    @staticmethod
    async def _invoke_callback_and_return(callback: Callable, msg: MessageContract):
        await callback(msg)
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
        """
        As listener is registered to channel at init time, you have to await object construction itself:

            my_listener = **await** SimpleDistributedApplicationListener(my_channel)

        """
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

        They should return a list of Messages corresponding to response to action requested.

        Reserved actions are 'start', 'stop'.
        Receiving a message with one of these types will fire corresponding action.

        """
        if action in self.__internal_actions:
            raise KeyError(f'Trying to set an internal action {action}')
        self.__actions[name] = action

    async def dispatch_to(self, receiver: MessageQueueListener, msg: MessageContract):
        signed_message = SignedMessage(sender_id=self.id, msg_type=msg.type, msg_payload=msg.payload)
        await self.__channel.dispatch(receiver.id, signed_message)

    async def on_message(self, msg: SignedMessage) -> None:
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
                await self.__channel.dispatch(msg.sender_id, signed_response)
        except KeyError:
            logger.debug(f'Unknown action {msg.type}')

class SimpleDistributedApplicationChannel(SSEChannel):

    async def register_listener(self, listener: SimpleDistributedApplicationListener):
        listener.set_channel(self)
        return await super().register_listener(listener)