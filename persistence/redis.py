import json
from json import JSONDecodeError

import redis

from uuid import uuid4
from eric_sse.message import Message
from eric_sse.queue import Queue, AbstractMessageQueueFactory
from persistence import RepositoryError

class RedisQueue(Queue):

    def __init__(self, **kwargs):
        """
        :param kwargs: Arguments accepted by redis.Redis constructor
        """
        self.id = str(uuid4())
        self.__client = redis.Redis(kwargs)

    def pop(self) -> Message:
        try:
            value = json.loads(self.__client.lpop(self.id))
        except redis.exceptions.ResponseError as e:
            raise RepositoryError(e)
        except JSONDecodeError as e:
            raise RepositoryError(e)

        msg = Message(type=value['type'], payload=value['payload'])
        return msg

    def push(self, msg: Message) -> None:
        value = json.dumps({'type': msg.type, 'payload': msg.payload})
        try:
            self.__client.rpush(value)
        except redis.exceptions.ResponseError as e:
            raise RepositoryError(e)


class RedisQueueFactory(AbstractMessageQueueFactory):
    def create(self) -> Queue:
        return RedisQueue()
