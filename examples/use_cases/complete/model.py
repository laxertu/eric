from dataclasses import dataclass
from eric_sse.message import MessageContract
from eric_sse.prefabs import SSEChannel


@dataclass
class Forecast:
    temperature: float

@dataclass
class ForecastNotification(MessageContract):
    forecast: Forecast

    @property
    def type(self) -> str:
        return "forecast"

    @property
    def payload(self) -> dict | list | str | int | float | None:
        return self.__dict__


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


