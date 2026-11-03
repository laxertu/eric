"""
Messaging patterns built on queues and :mod:`~eric_sse.handlers`.
"""
import traceback

import eric_sse
from eric_sse.handlers import QueuingErrorHandler, ListenerErrorHandler
from eric_sse.message import MessageContract
from eric_sse.queues import Queue, InMemoryQueue

logger = eric_sse.get_logger()


class DeadLetter(MessageContract):
    """
    A message that could not be delivered or processed, plus where it was going and why it failed.

    It wraps the original message: :attr:`type` and :attr:`payload` are the original ones,
    and :attr:`message` keeps its class, e.g. a :class:`~eric_sse.message.UniqueMessage` with its id.

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

    def __init__(self, queue: Queue | None = None):
        self.__queue = queue if queue is not None else InMemoryQueue()

    @property
    def queue(self) -> Queue:
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
