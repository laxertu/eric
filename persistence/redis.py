import json
from json import JSONDecodeError

import redis

from uuid import uuid4
from eric_sse.entities import Message, UniqueMessage, Queue
from persistence import RepositoryError

class RedisQueue(Queue):

    def __init__(self, host: str, port: int, db: int, password: str = None):
        self.id = str(uuid4())
        self.__client = redis.Redis(host=host, port=port, db=db, password=password)

    def pop(self) -> UniqueMessage:
        try:
            value = json.loads(self.__client.lpop(self.id))
        except redis.exceptions.ResponseError as e:
            raise RepositoryError(e)
        except JSONDecodeError as e:
            raise RepositoryError(e)

        msg = Message(type=value['type'], payload=value['payload'])
        return UniqueMessage(message_id=value['id'], sender_id=value['sender_id'], message=msg)

    def add(self, msg: UniqueMessage) -> None:
        value = json.dumps({'id': msg.id, 'sender_id': msg.sender_id, 'type': msg.type, 'payload': msg.payload})
        try:
            self.__client.rpush(value)
        except redis.exceptions.ResponseError as e:
            raise RepositoryError(e)
