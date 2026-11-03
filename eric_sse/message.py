from abc import ABC, abstractmethod

class MessageContract(ABC):
    """
    Contract class for messages

    A message is just a container of information identified by a type.
    For validation purposes you can override its :meth:`~eric_sse.listener.MessageQueueListener.on_message` method.

    """
    @property
    @abstractmethod
    def type(self) -> str:
        """Message type"""
        ...

    @property
    @abstractmethod
    def payload(self) -> dict | list | str | int | float | None:
        """Message payload"""
        ...

    @property
    def id(self) -> str | None:
        """Optional message identifier, e.g. the "id" field of an SSE event. None if the message has none."""
        return None


class Message(MessageContract):
    """
    Models a simple message

    :param str msg_type: Message type.
    :param msg_payload: Message payload.
    :param str | None msg_id: Optional message identifier, see :attr:`~eric_sse.message.MessageContract.id`.
    """
    def __init__(
            self,
            msg_type: str,
            msg_payload: dict | list | str | int | float | None = None,
            msg_id: str | None = None
    ) -> None:
        self._type = msg_type
        self._payload = msg_payload
        self._id = msg_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self._payload

    @property
    def id(self) -> str | None:
        return self._id


class SignedMessage(Message):
    """Message plus sender id"""

    def __init__(
            self,
            sender_id: str,
            msg_type: str,
            msg_payload: dict | list | str | int | float | None = None,
            msg_id: str | None = None
    ):
        super().__init__(msg_type, msg_payload, msg_id)
        self.__sender_id = sender_id

    @property
    def sender_id(self) -> str:
        """Returns the id of the listener that sent the message"""
        return self.__sender_id
