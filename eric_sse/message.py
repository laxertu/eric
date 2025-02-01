from abc import ABC, abstractmethod

class MessageContract(ABC):
    """
    Models a message

    It's just a container of information identified by a type.
    For validation purposes you can override MessageQueueListener.on_message
    """

    @property
    @abstractmethod
    def type(self) -> str:
        ...

    @property
    @abstractmethod
    def payload(self) -> dict | list | str | int | float | None:
        ...


class Message(MessageContract):
    """
    Models a message

    It's just a container of information identified by a type.
    For validation purposes you can override MessageQueueListener.on_message
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
    __message: Message
    __sender_id: str | None = None

    def __init__(self, message_id: str, message: Message, sender_id: str = None) -> None:
        self.__id = message_id
        self.__message = message
        self.__sender_id = sender_id

    @property
    def id(self) -> str:
        return str(self.__id)

    @property
    def type(self) -> str:
        return  self.__message.type

    @property
    def sender_id(self) -> str:
        return self.__sender_id

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self.__message.payload


class SignedMessage(Message):
    """A wrapper that adds sender id"""

    def __init__(self, sender_id: str, msg_type: str, msg_payload: dict | list | str | int | float | None = None):
        super().__init__(msg_type, msg_payload)
        self.__sender_id = sender_id

    @property
    def sender_id(self) -> str:
        return self.__sender_id

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return {'sender_id': self.__sender_id, 'payload': self._payload}

