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

    Concrete implementations of :class:`Queue` should wrap here the unexpected exceptions they catch before raising, and
    an :class:`eric_sse.exception.NoMessagesException` when a pop is requested on an empty queue.
    """
    ...
