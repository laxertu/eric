from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Callable, AsyncIterable, Iterator

from eric_sse import get_logger
from eric_sse.entities import AbstractChannel, MessageQueueListener
from eric_sse.message import Message, SignedMessage, MessageContract
from eric_sse.exception import NoMessagesException
from eric_sse.queue import AbstractMessageQueueFactory

logger = get_logger()


class SSEChannel(AbstractChannel):
    """
    SSE streaming channel.
    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format

    Currently, 'id' field is not supported.

    :param int stream_delay_seconds:
    :param int retry_timeout_milliseconds:
    :param eric_sse.queue.AbstractMessageQueueFactory queues_factory:
    """

    def __init__(
            self,
            stream_delay_seconds: int = 0,
            retry_timeout_milliseconds: int = 5,
            queues_factory: AbstractMessageQueueFactory = None
    ):
        super().__init__(stream_delay_seconds=stream_delay_seconds, queues_factory=queues_factory)
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

    def __init__(self, max_workers: int, stream_delay_seconds: int = 0):
        """
        :param max_workers: Num of workers to use
        :param stream_delay_seconds: Can be used to limit response rate of streaming. Only applies to message_stream calls.
        """
        super().__init__(stream_delay_seconds=stream_delay_seconds)
        self.max_workers = max_workers

    async def process_queue(self, l: MessageQueueListener) -> AsyncIterable[dict]:
        """
        Asynchronously processes messages from a listener's queue and yields adapted results.
        
        Args:
            l: The message queue listener whose messages will be processed.
        
        Yields:
            Dictionaries representing processed messages, adapted for downstream consumption.
        """

        async def event_generator(listener: MessageQueueListener) -> AsyncIterable[dict]:
            """
            Asynchronously yields adapted results for each processed message from a listener's queue.
            
            Iterates over completed message processing tasks and yields each result as a dictionary
            adapted for downstream consumption.
            """
            for task_result in as_completed(self.__schedule_tasks(listener)):
                yield self.adapt(task_result.result())

        return event_generator(listener=l)

    def __schedule_tasks(self, listener: MessageQueueListener) -> Iterator[Future]:
        """
        Submits message processing tasks from a listener's queue to a thread pool executor.
        
        Yields a Future for each submitted task, which processes a message using the listener's callback. Stops when the queue is empty.
        """
        with ThreadPoolExecutor(self.max_workers) as e:
            there_are_pending_messages = True
            while there_are_pending_messages:
                try:
                    msg = self._get_queue(listener.id).pop()
                    yield e.submit(self.__invoke_callback_and_return, listener.on_message, msg)

                except NoMessagesException:
                    there_are_pending_messages = False

    @staticmethod
    def __invoke_callback_and_return(callback: Callable[[MessageContract], None], msg: MessageContract):
        callback(msg)
        return msg

    def adapt(self, msg: Message) -> dict:
        return {
            "event": msg.type,
            "data": msg.payload
        }


class SimpleDistributedApplicationListener(MessageQueueListener):
    """Listener for distributed applications"""

    def __init__(self, channel: AbstractChannel):
        super().__init__()
        self.__channel = channel
        self.__actions: dict[str, Callable[[MessageContract], list[MessageContract]]] = dict()
        self.__internal_actions: dict[str, Callable[[], None]] = {
            'start': self.start_sync,
            'stop': self.stop_sync,
            'remove': self.remove_sync
        }
        channel.register_listener(self)

    def set_action(self, name: str, action: Callable[[MessageContract], list[MessageContract]]):
        """
        Registers a user-defined action to handle messages of a specific type.
        
        The provided callable will be invoked when a message with the given type is processed,
        and should return a list of response messages. Reserved action names ('start', 'stop',
        'remove') cannot be overridden.
        
        Raises:
            KeyError: If attempting to set an action with a reserved name.
        """
        if action in self.__internal_actions:
            raise KeyError(f'Trying to set an internal action {action}')
        self.__actions[name] = action

    def dispatch_to(self, receiver: MessageQueueListener, msg: MessageContract):
        """
        Sends a signed message to the specified receiver via the associated channel.
        
        The message is wrapped in a SignedMessage containing the sender's ID before dispatch.
        """
        signed_message = SignedMessage(sender_id=self.id, msg_type=msg.type, msg_payload=msg.payload)
        self.__channel.dispatch(receiver.id, signed_message)

    def on_message(self, msg: SignedMessage) -> None:
        """
        Handles an incoming signed message by executing the corresponding action.
        
        If the message type matches an internal action, executes it. Otherwise, invokes the registered user-defined action for the message type and dispatches any response messages back to the original sender. Logs a debug message if the message type is unknown.
        """
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

    def remove_sync(self):
        """Stop and unregister"""
        self.stop_sync()
        self.__channel.remove_listener(self.id)