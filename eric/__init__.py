from logging import getLogger
from dataclasses import dataclass

class InvalidSessionException(Exception):
    ...

class InvalidListenerException(Exception):
    ...

class NoMessagesException(Exception):
    ...

logger = getLogger()

@dataclass
class Message:
    type: str
    payload: dict | list | str | None = None


class MessageQueueListener:
    @property
    def id(self):
        return str(id(self))


class Eric:

    QUEUES: dict[str: dict[str: list[Message]]] = {}

    def register_session(self, session_id: str):
        self.QUEUES[session_id] = {}

    def add_listener(self, session_id: str, listener: MessageQueueListener):
        self.QUEUES[session_id][listener.id] = []

    def get(self, session_id: str, listener_id: str) -> Message:
        try:
            return self.__get_queue(session_id, listener_id).pop(0)
        except IndexError:
            raise NoMessagesException

    def __get_queue(self, session_id: str, listener_id: str) -> list[Message]:
        try:
            _ = self.QUEUES[session_id]
        except KeyError:
            raise InvalidSessionException(f"Invalid session {session_id}")

        try:
            _ = self.QUEUES[session_id][listener_id]
        except KeyError:
            raise InvalidListenerException(f"Invalid listener {listener_id}")

        return self.QUEUES[session_id][listener_id]


    def add(self, session_id: str, listener_id: str, msg: Message):
        self.__get_queue(session_id, listener_id).append(msg)
        logger.debug(f"Pending {len(self.QUEUES[session_id][listener_id])} messages")

    def broadcast(self, session_id: str, msg: Message):
        for listener_id in self.QUEUES[session_id].keys():
            logger.debug(f"Broadcasting {msg.type} to listener {listener_id}")
            self.add(session_id=session_id, listener_id=listener_id, msg=msg)

    def delete_session(self, session_id: str):
        del self.QUEUES[session_id]
