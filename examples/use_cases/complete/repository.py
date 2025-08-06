from typing import Iterable

from eric_sse.persistence import ChannelRepositoryInterface, PersistableListener, ObjectAsKeyValuePersistenceMixin, \
    ConnectionRepositoryInterface, PersistableConnection
from eric_sse.exception import RepositoryError, InvalidChannelException

from eric_sse.queues import Queue, InMemoryQueue
from .model import ForecastChannel


class DatabaseException(Exception):
    pass

class RowNotFoundException(Exception):
    pass

# Internals
class _DataBase:
    def __init__(self):
        self.__rows: dict[str, dict] = {}

    def upsert(self, key: str, data: dict) -> None:
        self.__rows[key] = data

    def get(self, key: str) -> dict:
        try:
            return self.__rows[key]
        except KeyError:
            raise RowNotFoundException

    def get_all(self) -> Iterable[tuple[str, dict]]:
        for key, value in self.__rows.items():
            yield key, value


    def delete(self, key: str) -> None:
        del self.__rows[key]

# Integration

class ForecastsNotificationRepository(ConnectionRepositoryInterface):
    def __init__(self) -> None:
        self.__db = _DataBase()

    def create_queue(self, listener_id: str) -> Queue:
        return InMemoryQueue()

    def persist(self, channel_id: str, connection: PersistableConnection) -> None:
        self.__db.upsert(channel_id, {})

    def load_all(self) -> Iterable[PersistableConnection]:
        for key, value in self.__db.get_all():
            raw = self.__db.get(key)
            connection = PersistableConnection(queue=self.create_queue(raw['id']), listener=PersistableListener())
            connection.queue.setup_by_dict(raw)
            yield connection


    def load(self, channel_id: str) -> Iterable[PersistableConnection]:
        pass

    def delete(self, channel_id: str, listener_id: str) -> None:
        pass


class ForecastChannelRepository(ChannelRepositoryInterface):
    def __init__(self):
        self.__db = _DataBase()

    def get_channel(self, channel_id: str) -> ForecastChannel:
        try:
            constructor_params = self.__db.get(channel_id)['constructor_params']
            setup_params = self.__db.get(channel_id)['setup_params']
            channel = ForecastChannel(**constructor_params)

            channel.setup_by_dict(setup_params)

            return channel
        except RowNotFoundException:
            raise InvalidChannelException
        except Exception as e:
            raise RepositoryError(e) from e

    def delete_listener(self, channel_id: str, listener_id: str) -> None:
        try:
            self.__db.delete(listener_id)
        except DatabaseException as e:
            raise RepositoryError(e) from e

    def load(self) -> Iterable[ObjectAsKeyValuePersistenceMixin]:
        for k, v in self.__db.get_all():
            yield self.get_channel(k)


    def persist(self, persistable: ForecastChannel):
        try:
            kv_data = {
                'constructor_params': persistable.kv_constructor_params_as_dict,
                'setup_params': persistable.kv_value_as_dict,
            }
            self.__db.upsert(persistable.kv_key, kv_data)
        except DatabaseException as e:
            raise RepositoryError(e) from e

    def delete(self, key: str):
        try:
            self.__db.delete(key)
        except DatabaseException as e:
            raise RepositoryError(e) from e