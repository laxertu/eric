from abc import ABC, abstractmethod

class MessageContract(ABC):
    """
    Contract class for messages

    A message is just a container of information identified by a type.
    For validation purposes you can override :class:`eric_sse.entities.MessageQueueListener.on_message`

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


class Message(MessageContract):
    """
    Models a simple message
    """
    def __init__(self, msg_type: str, msg_payload: dict | list | str | int | float | None = None) -> None:
        self._type = msg_type
        self._payload = msg_payload

    @property
    def type(self) -> str:
        return self._type

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self._payload


class UniqueMessage(MessageContract):
    """Messages plus an unique identifier"""
    __message: MessageContract
    __sender_id: str | None = None

    def __init__(self, message_id: str, message: MessageContract, sender_id: str = None) -> None:
        self.__id = message_id
        self.__message = message
        self.__sender_id = sender_id

    @property
    def id(self) -> str:
        """Unique message identifier"""
        return str(self.__id)

    @property
    def type(self) -> str:
        return  self.__message.type

    @property
    def sender_id(self) -> str:
        """Returns the id of the listener that sent the message"""
        return self.__sender_id

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self.__message.payload


class SignedMessage(Message):
    """Message plus sender id"""

    def __init__(self, sender_id: str, msg_type: str, msg_payload: dict | list | str | int | float | None = None):
        super().__init__(msg_type, msg_payload)
        self.__sender_id = sender_id

    @property
    def sender_id(self) -> str:
        """Returns the id of the listener that sent the message"""
        return self.__sender_id


