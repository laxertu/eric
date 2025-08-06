from dataclasses import dataclass
from eric_sse.message import MessageContract

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