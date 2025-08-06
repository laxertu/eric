from eric_sse.message import MessageContract
from eric_sse.persistence import PersistableQueue
from eric_sse.prefabs import SSEChannel
from eric_sse.queues import InMemoryQueue
from examples.use_cases.complete.model import Forecast, ForecastNotification
from examples.use_cases.complete.repository import ForecastChannelRepository

class ForecastChannel(SSEChannel):


    @property
    def kv_constructor_params_as_dict(self) -> dict:
        """we are just interested to SSE service settings"""
        return {
            'channel_id': self.id,
            'stream_delay_seconds': self.stream_delay_seconds,
            'retry_timeout_milliseconds': self.retry_timeout_milliseconds,
        }

    def notify(self, forecast: Forecast):
        self.broadcast(ForecastNotification(forecast))


class ForecastQueue(PersistableQueue):
    """A fake queue for demonstration purposes. Internally wraps an InMemoryQueue"""
    def __init__(self, consumer_id: str):
        self.__listener_id = consumer_id
        self.__queue = InMemoryQueue()

    def pop(self) -> MessageContract:
        return self.__queue.pop()

    def push(self, message: MessageContract) -> None:
        self.__queue.push(message)

    @property
    def kv_key(self) -> str:
        return self.__listener_id

    @property
    def kv_value_as_dict(self) -> dict:
        return {
            'consumer_id': self.__listener_id,
            'queue': self.__queue,
        }

    def setup_by_dict(self, setup: dict):
        self.__listener_id = setup['consumer_id']
        self.__queue = InMemoryQueue()

    @property
    def kv_constructor_params_as_dict(self) -> dict:
        return {
            'consumer_id': self.__listener_id,
        }

class Application:
    """Here you can expose whatever, for example channel creation"""
    def __init__(self):
        self.repository = ForecastChannelRepository()

    def create_channel(self):
        channel = ForecastChannel()
        self.repository.persist(channel)
        return channel
