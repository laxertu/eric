from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Callable, AsyncIterable, Iterator

from eric_sse import get_logger
from eric_sse.entities import AbstractChannel, Message, MessageQueueListener, SignedMessage

logger = get_logger()


class SSEChannel(AbstractChannel):
    """
    SSE streaming channel.
    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format

    Currently, 'id' field is not supported.
    """

    def __init__(self, stream_delay_seconds: int = 0, retry_timeout_milliseconds: int = 5):
        """
        :param stream_delay_seconds:
        :param retry_timeout_milliseconds:
        """
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.retry_timeout_milliseconds = retry_timeout_milliseconds

    def adapt(self, msg: Message) -> dict:
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }


class DataProcessingChannel(AbstractChannel):
    """
    Channel intended for concurrent processing of data.

    :param max_workers: Num og workers to use
    :param stream_delay_seconds: Can be used to limit response rate of streamings. Only applies to message_stream calls.

    Relies on concurrent.futures.ThreadPoolExecutor.
    Just override **adapt** method to control output returned to clients

    MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.  
    """

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0):
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.max_workers = max_workers

    async def process_queue(self, l: MessageQueueListener) -> AsyncIterable[dict]:
        """Launches the processing of the given listener's queue"""

        async def event_generator(listener: MessageQueueListener) -> AsyncIterable[dict]:
            for f in as_completed(self.__prepare_executor(listener)):
                yield self.adapt(f.result())

        return event_generator(listener=l)

    def __prepare_executor(self, listener: MessageQueueListener) -> Iterator[Future]:
        with ThreadPoolExecutor(self.max_workers) as e:
            there_are_peding_messages = True
            while there_are_peding_messages:
                try:
                    msg = self.queues[listener.id].pop(0)
                    yield e.submit(self.__invoke_callback_and_return, listener.on_message, msg)

                except IndexError:
                    there_are_peding_messages = False

    @staticmethod
    def __invoke_callback_and_return(callback: Callable[[Message], None], msg: Message):
        callback(msg)
        return msg

    def adapt(self, msg: Message) -> dict:
        return {
            "event": msg.type,
            "data": msg.payload
        }


class SimpleDistributedApplicationListener(MessageQueueListener):
    """Listener for distrubuted applications"""

    def __init__(self, channel: AbstractChannel):
        super().__init__()
        self.__channel = channel
        self.__actions: dict[str, Callable[[Message], list[Message]]] = dict()
        channel.register_listener(self)
        self.__internal_actions: dict[str, Callable[[], None]] = {
            'stop': self.stop_sync
        }

    def set_action(self, name: str, action: Callable[[Message], list[Message]]):
        """
        Hooks a callable to a string key.

        Callables are selected when listener processes the message depending on it's type

        :param name:
        :param action:
        :return:
        """
        if action in self.__internal_actions:
            raise KeyError(f'Trying to set an internal action {action}')
        self.__actions[name] = action

    def on_message(self, msg: Message) -> None:
        try:
            try:
                self.__internal_actions[msg.type]()
                return
            except KeyError:
                pass

            msgs = self.__actions[msg.type](msg)
            for response in msgs:
                signed_response = SignedMessage(sender_id=self.id, msg_type=response.type, msg_payload=response.payload)
                self.__channel.dispatch(msg.payload['sender_id'], signed_response)
        except KeyError:
            logger.error(f'Unknown action {msg.type}')
