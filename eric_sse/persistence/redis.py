import json

import redis

from eric_sse.entities import Message, UniqueMessage
from eric_sse.persistence import Repository, RepositoryError

class RedisRepository(Repository):

    def __init__(self, host: str, port: int, db: int, password: str = None):
        self.__client = redis.Redis(host=host, port=port, db=db, password=password)

    def set(self, msg: UniqueMessage):
        value = json.dumps({'id': msg.id, 'sender_id': msg.sender_id, 'type': msg.type, 'payload': msg.payload})
        self.__client.set(name=msg.id, value=value)

    def get(self, key: str) -> UniqueMessage:
        value = json.loads(self.__client.get(name=key))
        msg = Message(type=value['type'], payload=value['payload'])
        return UniqueMessage(message_id=value['id'], sender_id=value['sender_id'], message=msg)

    def rm(self, key: str):
        try:
            self.__client.delete(key)
        except redis.exceptions.ResponseError as e:
            raise RepositoryError(e)
