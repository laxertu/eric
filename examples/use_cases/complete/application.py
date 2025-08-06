from typing import AsyncIterable

from examples.use_cases.complete.model import Forecast, ForecastNotification, ForecastChannel
from examples.use_cases.complete.repository import ForecastChannelRepository


class Application:
    def __init__(self):
        self.repository = ForecastChannelRepository()

    def create_channel(self):
        channel = ForecastChannel()
        self.repository.persist(channel)
        return channel

    def subscribe(self, channel: ForecastChannel):
        listener = channel.add_listener()
        self.repository.persist(channel)
        return listener

    def notify(self, channel_id: str, forecast: Forecast):
        self.repository.get_channel(channel_id).notify(forecast)

    async def listen(self, channel_id: str, listener_id: str) -> AsyncIterable[ForecastNotification]:
        channel = self.repository.get_channel(channel_id)
        listener = channel.get_listener(listener_id)
        listener.start()
        async for forecast_notification in channel.message_stream(listener=listener):
            yield forecast_notification.forecast.temperature




