from abc import ABC, abstractmethod
from typing import Iterable
from importlib import import_module

from eric_sse.exception import RepositoryError

class ItemNotFound(Exception):
    pass



class ObjectAsKeyValuePersistenceMixin(ABC):
    """
    Adds KV persistence support.

    By implementing this abstract mixin should be possible to persist every object that is not directly
    serializable by pickle, for example, if your Queues implementation wraps some incompatible dependency, e.g. a Redis client.

    For this reason, the idea is that dict values should be serializable by pickle too.

    see :func:`~eric_sse.persistence.importlib_create_instance`
    """
    @property
    def kv_as_dict(self) -> dict:
        return {
            'class_path': self.kv_class_absolute_path,
            'constructor_parameters': self.kv_constructor_params_as_dict,
            'setup_dict': self.kv_setup_values_as_dict
        }

    @property
    @abstractmethod
    def kv_key(self) -> str:
        """The key to use when persisting object"""
        ...

    @property
    @abstractmethod
    def kv_setup_values_as_dict(self) -> dict:
        """Returns value that will be persisted as a dictionary."""
        ...

    @abstractmethod
    def kv_setup_by_dict(self, setup: dict):
        """Does necessary post-creation setup of object given its persisted values"""
        ...

    @property
    def kv_class_absolute_path(self) -> str:
        """Returns class full path as string"""
        return f'{self.__module__}.{type(self).__name__}'

    @property
    @abstractmethod
    def kv_constructor_params_as_dict(self) -> dict:
        """Class constructor parameters as dict"""
        ...


class KvStorageEngine(ABC):

    @abstractmethod
    def fetch_by_prefix(self, prefix: str) -> Iterable[any]:
        ...

    @abstractmethod
    def fetch_all(self) -> Iterable[any]:
        ...

    @abstractmethod
    def upsert(self, key: str, value: any):
        ...

    @abstractmethod
    def fetch_one(self, key: str) -> any:
        ...

    @abstractmethod
    def delete(self, key: str):
        ...


class ObjectRepositoryInterface(ABC):
    """Every exception raised by concrete implementations show be wrapped inside a :class:`~eric_sse.exception.RepositoryError`
    """

    @abstractmethod
    def load_all(self) -> Iterable[ObjectAsKeyValuePersistenceMixin]:
        """Returns an Iterable of all persisted objects of correspondant concrete implementation."""
        ...

    @abstractmethod
    def load_one(self, key: str) -> ObjectAsKeyValuePersistenceMixin:
        ...

    @abstractmethod
    def persist(self, persistable: ObjectAsKeyValuePersistenceMixin):
        ...

    @abstractmethod
    def delete(self, key: str):
        ...

def importlib_create_instance(class_full_path: str, constructor_params: dict, setup_values: dict) -> ObjectAsKeyValuePersistenceMixin:
    """
    Creates a persistable class instance given a persisted value and executes its setup_by_dict method

    see :func:`~eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_setup_values_as_dict`
    """
    path_parts = class_full_path.split('.')
    module = '.'.join(path_parts[:-1])
    klass = path_parts[-1]

    module_object = import_module(module)
    obj: ObjectAsKeyValuePersistenceMixin = getattr(module_object, klass)(**constructor_params)

    try:
        assert isinstance(obj, ObjectAsKeyValuePersistenceMixin)
    except AssertionError as e:
        raise RepositoryError(e) from e

    obj.kv_setup_by_dict(setup_values)

    return obj

def create_instance(kv_values: ObjectAsKeyValuePersistenceMixin) -> ObjectAsKeyValuePersistenceMixin:
    return importlib_create_instance(
        class_full_path=kv_values.kv_class_absolute_path,
        constructor_params=kv_values.kv_constructor_params_as_dict,
        setup_values=kv_values.kv_setup_values_as_dict
    )
