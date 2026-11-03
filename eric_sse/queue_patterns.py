"""
Messaging patterns built on queues and :mod:`~eric_sse.handlers`.
"""
import threading
import time
import traceback

import eric_sse
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.message import MessageContract
from eric_sse.queues import Queue, InMemoryQueue
from eric_sse.exception import ItemNotFound
from eric_sse.repository import KvStorage, InMemoryStorage

logger = eric_sse.get_logger()


class DeadLetter(MessageContract):
    """
    A message that could not be delivered or processed, plus where it was going and why it failed.

    It wraps the original message: :attr:`id`, :attr:`type` and :attr:`payload` are the original ones,
    and :attr:`message` keeps its class, e.g. a :class:`~eric_sse.message.SignedMessage` with its sender.

    To redeliver it: ``channel.dispatch(dead_letter.listener_id, dead_letter.message)``.

    :param str listener_id: Id of the listener the message was meant for.
    :param ~eric_sse.message.MessageContract message: The original message.
    :param str error: Description of the error, e.g. ``repr()`` of the exception.
    """

    def __init__(self, listener_id: str, message: MessageContract, error: str):
        self.__listener_id = listener_id
        self.__message = message
        self.__error = error

    @property
    def listener_id(self) -> str:
        """Id of the listener the message was meant for."""
        return self.__listener_id

    @property
    def message(self) -> MessageContract:
        """The original message."""
        return self.__message

    @property
    def error(self) -> str:
        """Description of the error."""
        return self.__error

    @property
    def id(self) -> str | None:
        return self.__message.id

    @property
    def type(self) -> str:
        return self.__message.type

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self.__message.payload


class DeadLetterHandler(QueuingErrorHandler, ListenerErrorHandler):
    """
    Dead Letter pattern: messages that could not be delivered or processed are pushed to a dead letter queue,
    wrapped in a :class:`DeadLetter`.

    A message is dead-lettered when:

    * pushing it to a listener's queue fails, see :meth:`handle_push_error`;
    * the listener's :meth:`~eric_sse.listener.MessageQueueListener.on_message` fails, see :meth:`handle_on_message_error`.

    Pop errors are not dead-lettered: no message is available when they occur.

    Register the same instance for both kinds of errors::

        dead_letters = DeadLetterHandler()
        channel.add_queuing_error_handler(dead_letters)
        channel.add_listener_error_handler(dead_letters)

    or, for every channel of a repository, with
    :meth:`~eric_sse.builder.ChannelRepositoryBuilder.queuing_error_handler` and
    :meth:`~eric_sse.builder.ChannelRepositoryBuilder.listener_error_handler`.

    If pushing to the dead letter queue fails too, the error is logged and the message is lost:
    the handler never raises, so the original error is the one the channel re-raises or logs.

    :param ~eric_sse.queues.Queue queue: The dead letter queue. Defaults to an :class:`~eric_sse.queues.InMemoryQueue`.
    """

    def __init__(self, queue: Queue[DeadLetter] | None = None):
        self.__queue: Queue[DeadLetter] = queue if queue is not None else InMemoryQueue()

    @property
    def queue(self) -> Queue[DeadLetter]:
        """The dead letter queue, e.g. to inspect or redeliver its messages."""
        return self.__queue

    def handle_push_error(self, listener_id: str, msg: MessageContract, exception: Exception) -> None:
        self._dead_letter(listener_id, msg, exception)

    def handle_on_message_error(self, listener_id: str, msg: MessageContract, exception: Exception) -> None:
        self._dead_letter(listener_id, msg, exception)

    def _dead_letter(self, listener_id: str, msg: MessageContract, exception: Exception) -> None:
        """Pushes **msg** to the dead letter queue, wrapped in a :class:`DeadLetter`. Override to change what is stored."""
        try:
            self.__queue.push(DeadLetter(listener_id=listener_id, message=msg, error=repr(exception)))
        except Exception as e:
            logger.debug(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            logger.error(f"Dead letter lost after {exception!r}: {e!r}")


class ReliableMessage(MessageContract):
    """
    A message popped from a :class:`ReliableQueue`: the original message plus an id to acknowledge it with.

    :attr:`type` and :attr:`payload` are the original ones, and :attr:`message` keeps its class.

    :param str message_id: Id to pass to :meth:`ReliableQueue.ack` or :meth:`ReliableQueue.nack`.
    :param ~eric_sse.message.MessageContract message: The original message.
    :param int deliveries: How many times the message has been popped, this time included.
    """

    def __init__(self, message_id: str, message: MessageContract, deliveries: int = 0):
        self.__id = message_id
        self.__message = message
        self.__deliveries = deliveries

    @property
    def id(self) -> str:
        """Id to acknowledge the message with. It replaces the original message's id, if any."""
        return self.__id

    @property
    def message(self) -> MessageContract:
        """The original message."""
        return self.__message

    @property
    def deliveries(self) -> int:
        """How many times the message has been popped: more than 1 means it is a redelivery."""
        return self.__deliveries

    @property
    def type(self) -> str:
        return self.__message.type

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self.__message.payload


class ReliableQueue(Queue[ReliableMessage]):
    """
    Reliable Queue pattern: a popped message isn't removed, it is moved to an in-flight storage until it is acknowledged.

    * :meth:`pop` and :meth:`wait_pop` return a :class:`ReliableMessage`;
    * :meth:`ack` removes it for good, once it has been handled, e.g. when the client confirms it got it;
    * :meth:`nack` puts it back in the queue at once;
    * messages not acknowledged within **visibility_timeout** seconds are put back in the queue by :meth:`requeue_expired`,
      that :meth:`pop` and :meth:`wait_pop` call before popping.

    Delivery is *at least once*: a message acknowledged after its visibility timeout may already have been put back,
    and is delivered again. Requeued messages go to the end of the queue.

    It wraps another queue, that keeps the messages waiting to be popped, and a :class:`~eric_sse.repository.KvStorage`
    for in-flight messages. With durable ones, unacknowledged messages survive a restart.
    It can be pickled if both can, so it can be persisted by a queue repository.

    :param ~eric_sse.queues.Queue queue: Queue of messages waiting to be popped. Defaults to an :class:`~eric_sse.queues.InMemoryQueue`.
    :param float | None visibility_timeout: Seconds a popped message can stay unacknowledged. None: until :meth:`nack`.
    :param ~eric_sse.repository.KvStorage in_flight: Storage of popped messages not yet acknowledged. Defaults to an :class:`~eric_sse.repository.InMemoryStorage`.
    """

    def __init__(
            self,
            queue: Queue[ReliableMessage] | None = None,
            visibility_timeout: float | None = 30.0,
            in_flight: KvStorage | None = None,
    ):
        self.__queue: Queue[ReliableMessage] = queue if queue is not None else InMemoryQueue()
        self.__visibility_timeout = visibility_timeout
        self.__in_flight = in_flight if in_flight is not None else InMemoryStorage()
        self.__lock = threading.Lock()

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        del state['_ReliableQueue__lock']
        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)
        self.__lock = threading.Lock()

    def push(self, message: MessageContract) -> None:
        """Pushes **message**, wrapped in a :class:`ReliableMessage` with a new id."""
        self.__queue.push(ReliableMessage(eric_sse.generate_uuid(), message))

    def pop(self, timeout: float = 0) -> ReliableMessage:
        self.requeue_expired()
        return self.__take(self.__queue.pop(timeout))

    async def wait_pop(self, timeout: float) -> ReliableMessage:
        self.requeue_expired()
        return self.__take(await self.__queue.wait_pop(timeout))

    def __take(self, queued: ReliableMessage) -> ReliableMessage:
        popped = ReliableMessage(queued.id, queued.message, queued.deliveries + 1)
        deadline = None if self.__visibility_timeout is None else time.time() + self.__visibility_timeout
        with self.__lock:
            self.__in_flight.upsert(popped.id, {'message': popped, 'deadline': deadline})
        return popped

    def __release(self, message_id: str) -> ReliableMessage | None:
        """Removes a message from in-flight ones and returns it, or None if it isn't in flight."""
        with self.__lock:
            try:
                entry = self.__in_flight.fetch_one(message_id)
            except ItemNotFound:
                return None
            self.__in_flight.delete(message_id)
        return entry['message']

    def ack(self, message_id: str) -> bool:
        """
        Acknowledges a popped message, that is removed for good.

        Returns False if it isn't in flight: unknown, already acknowledged, or put back in the queue.
        """
        return self.__release(message_id) is not None

    def nack(self, message_id: str) -> bool:
        """
        Puts a popped message back in the queue at once.

        Returns False if it isn't in flight: unknown, already acknowledged, or put back in the queue.
        """
        message = self.__release(message_id)
        if message is None:
            return False
        self.__queue.push(message)
        return True

    def requeue_expired(self) -> int:
        """Puts back in the queue messages not acknowledged within the visibility timeout. Returns how many."""
        if self.__visibility_timeout is None:
            return 0
        now = time.time()
        expired = [
            entry['message'].id for entry in self.__in_flight.fetch_all()
            if entry['deadline'] is not None and entry['deadline'] <= now
        ]
        return sum(1 for message_id in expired if self.nack(message_id))

    def in_flight(self) -> list[ReliableMessage]:
        """Popped messages not yet acknowledged."""
        return [entry['message'] for entry in self.__in_flight.fetch_all()]
