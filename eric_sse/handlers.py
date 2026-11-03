from eric_sse.message import MessageContract


class QueuingErrorHandler:
    """
    Handles errors raised by queues, see :meth:`~eric_sse.entities.AbstractChannel.add_queuing_error_handler`.

    Methods do nothing by default: override the ones you need.
    """

    def handle_push_error(self, listener_id: str, msg: MessageContract, exception: Exception) -> None:
        """Called when pushing **msg** to the queue of listener **listener_id** fails. The exception is re-raised afterwards."""
        pass

    def handle_pop_error(self, listener_id: str, exception: Exception) -> None:
        """Called when popping from the queue of listener **listener_id** fails. The exception is re-raised afterwards."""
        pass


class ListenerErrorHandler:
    """
    Handles errors raised by listeners, see :meth:`~eric_sse.entities.AbstractChannel.add_listener_error_handler`.

    Methods do nothing by default: override the ones you need.
    """

    def handle_on_message_error(self, listener_id: str, msg: MessageContract, exception: Exception) -> None:
        """
        Called when :meth:`~eric_sse.listener.MessageQueueListener.on_message` of listener **listener_id** fails.
        The exception is not re-raised: **msg** is delivered anyway.
        """
        pass
