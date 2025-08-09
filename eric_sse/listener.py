import eric_sse
from eric_sse.exception import RepositoryError
from eric_sse.message import MessageContract
from eric_sse.persistence import ObjectAsKeyValuePersistenceMixin

logger = eric_sse.get_logger()

class MessageQueueListener:
    """
    Base class for listeners.

    Optionally you can override on_message method if you need to inject code at message delivery time.
    """

    def __init__(self):
        self.id: str = eric_sse.generate_uuid()
        self.__is_running: bool = False

    def on_message(self, msg: MessageContract) -> None:
        """Event handler. It executes when a message is delivered to client"""
        pass

    def start(self) -> None:
        self.__is_running = True

    def stop(self) -> None:
        self.__is_running = False

    def is_running(self) -> bool:
        return self.__is_running


class PersistableListener(MessageQueueListener, ObjectAsKeyValuePersistenceMixin):
    """Gives KV persistence support to MessageQueueListener."""
    @property
    def kv_key(self) -> str:
        return self.id

    @property
    def kv_setup_values_as_dict(self) -> dict:
        return {
            'id': self.id,
            'is_running': self.is_running()
        }

    def kv_setup_by_dict(self, setup: dict):
        try:
            self.id = setup['id']
            if setup.get('is_running', False):
                self.start()
        except KeyError:
            raise RepositoryError(f'Invalid setup: {setup}')

    @property
    def kv_constructor_params_as_dict(self) -> dict:
        return {}
