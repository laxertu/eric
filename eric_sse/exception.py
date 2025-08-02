class InvalidChannelException(Exception):
    ...


class InvalidListenerException(Exception):
    ...


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
