class InvalidChannelException(Exception):
    ...


class InvalidListenerException(Exception):
    ...


class NoMessagesException(Exception):
    """Raised when trying to fetch from an empty queue"""
    ...


class InvalidMessageFormat(Exception):
    ...
