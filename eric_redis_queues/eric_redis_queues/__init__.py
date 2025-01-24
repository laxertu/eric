import json
from json import JSONDecodeError
from uuid import uuid4

from redis import Redis
from redis.exceptions import ResponseError

from eric_sse.exception import NoMessagesException
from eric_sse.message import Message
from eric_sse.queue import Queue, AbstractMessageQueueFactory


class RepositoryError(Exception):
    ...

class RedisQueue(Queue):
    def __init__(self, host='127.0.0.1', port=6379, db=0):
        self.id = str(uuid4())
        self.__client = Redis(host=host, port=port, db=db)

    def pop(self) -> Message:
        try:
            raw_value = self.__client.lpop(self.id)
            if raw_value is None:
                raise NoMessagesException
            value=json.loads(raw_value.decode())
            return Message(type=value['type'], payload=value['payload'])
        except ResponseError as e:
            raise RepositoryError(e)
        except JSONDecodeError as e:
            raise RepositoryError(e)

    def push(self, msg: Message) -> None:
        value = json.dumps({'type': msg.type, 'payload': msg.payload})
        try:
            self.__client.rpush(self.id, value)
        except ResponseError as e:
            raise RepositoryError(e)

    def delete(self) -> None:
        self.__client.delete(self.id)


class RedisQueueFactory(AbstractMessageQueueFactory):
    """
    Inject this class to Channels to enable Messages eric_redis_queues on a Redis database
    """
    def __init__(self, host='127.0.0.1', port=6379, db=0):
        self.__host: str = host
        self.__port: int = port
        self.__db: int = db

    def create(self) -> Queue:
        return RedisQueue(host=self.__host, port=self.__port, db=self.__db)
