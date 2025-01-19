from abc import ABC, abstractmethod

from eric_sse.entities import UniqueMessage

class Repository(ABC):
    @abstractmethod
    def set(self, msg: UniqueMessage):
        ...

    @abstractmethod
    def get(self, key: str) -> UniqueMessage:
        ...

    @abstractmethod
    def rm(self, key: str):
        ...
