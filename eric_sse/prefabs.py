from typing import Any, Callable, AsyncIterable, Iterator


from eric_sse import get_logger
from eric_sse.entities import AbstractChannel, Message, MessageQueueListener, MESSAGE_TYPE_CLOSED
from concurrent.futures import ThreadPoolExecutor, Future

logger = get_logger()

class SSEChannel(AbstractChannel):

    """
    SSE streaming channel.

    :param retry_timeout_milliseconds: Used to indicate waiting time to clients

    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format

    Currently, 'id' field is not supported.
    """
    def __init__(self, retry_timeout_milliseconds: int = 5):
        super().__init__()
        self.retry_timeout_milliseconds = retry_timeout_milliseconds

    def adapt(self, msg: Message) -> Any:
        return {
            "event": msg.type,
            "retry": self.retry_timeout_milliseconds,
            "data": msg.payload
        }


class DataProcessingChannel(AbstractChannel):
    """
    [Still experimental, it was never tested on some real use case] Channel intended for concurrent processing of data.

    :param max_workers: Num og workers to use
    :param stream_delay_seconds: Can be used to limit response rate of streamings

    Relies on concurrent.futures.ThreadPoolExecutor. 

    Just override **adapt** method to control output returned to clients


    MESSAGE_TYPE_CLOSED type is intended as end of stream. It should be considered as a reserved Message type.

    Note that callback execution order is not guaranteed
    """

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0):
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers

    async def process_queue(self, l: MessageQueueListener) -> AsyncIterable[dict]:
        """Launches the processing of the given listener's queue"""
        from concurrent.futures import as_completed
        async def event_generator(listener: MessageQueueListener) -> AsyncIterable[dict]:
            fs: Iterator[Future] = self._prepare_executor(listener)
            for f in as_completed(fs):
                yield self.adapt(f.result())

        return event_generator(listener=l)

    def _prepare_executor(self, listener: MessageQueueListener) -> Iterator[Future]:
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

    def notify_end(self):
        """Broadcasts a MESSAGE_TYPE_CLOSED Message"""
        self.broadcast(Message(type=MESSAGE_TYPE_CLOSED))


    def adapt(self, msg: Message) -> Any:
        """Models output returned to clients"""
        return {
            "event": msg.type,
            "data": msg.payload
        }

