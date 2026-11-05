class InvalidChannelException(Exception):
    ...

class InvalidConnectionException(Exception):
    ...

class InvalidListenerException(Exception):
    ...


class StoppedListenerException(Exception):
    """Raised when waiting for messages of a listener that is not running, see :meth:`~eric_sse.entities.AbstractChannel.deliver_next` and :meth:`~eric_sse.entities.AbstractChannel.wait_next`."""
    def __init__(self, listener_id: str):
        super().__init__(f'Listener {listener_id} is not running')


class InternalStreamError(Exception):
    """
    Stands for an unexpected error in a channel stream, without its details, that could expose internals to clients.
    See :meth:`~eric_sse.entities.AbstractChannel.adapt_error`.
    """
    def __init__(self):
        super().__init__('Internal error')


class NoMessagesException(Exception):
    """Raised when trying to fetch from an empty queue"""
    ...


class InvalidMessageFormat(Exception):
    ...


class RepositoryError(Exception):
    """
    Raised when an unexpected error occurs while trying to fetch messages from a queue.

    Concrete implementations of :class:`~eric_sse.persistence.ObjectRepositoryInterface` should wrap here the unexpected exceptions they catch before raising.
    """
    ...


class ItemNotFound(Exception):
    """Raised to inform that a key was not found in a repository"""
    def __init__(self, key: str):
        self.key = key
