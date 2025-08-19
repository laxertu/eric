"""
The simplest possible use of the persistence layer. Here unique dependency with it is with ChannelRepositoryInterface.
The rest of participants are from classes shipped from the library.

The following is a fake application with an in memory channel repository, and that just support channel creation and broadcasting
"""
from asyncio import run

from eric_sse.channel import PersistableChannel
from eric_sse.connection import Connection
from eric_sse.listener import MessageQueueListener
from eric_sse.prefabs import SSEChannel
from eric_sse.message import Message
from eric_sse.persistence import ObjectAsKeyValuePersistenceMixin

from eric_sse.inmemory import InMemoryStorage, InMemoryConnectionRepository
from eric_sse.queues import InMemoryQueue

from eric_sse.repository import AbstractPersistableChannelRepository, AbstractConnectionRepository


class PersistenceLayerConnectionRepository(AbstractConnectionRepository):

    def create_connection_instance(self, kv_stored: ObjectAsKeyValuePersistenceMixin) -> Connection:
        pass


class PersistenceLayerRepositoryImplementation(AbstractPersistableChannelRepository):
    """Fake repository"""

    def __init__(self):
        super().__init__(
            storage_engine=InMemoryStorage(),
            connections_repository=InMemoryConnectionRepository()
        )

    def create_instance(self, persisted_kv: dict) -> PersistableChannel:
        channel = SSEChannel(**persisted_kv[ObjectAsKeyValuePersistenceMixin.CONSTRUCTOR_PARAMETERS])
        channel.kv_setup_by_dict(persisted_kv[ObjectAsKeyValuePersistenceMixin.SETUP_DICT])

        return channel


class Application:
    def __init__(self):
        self.__channels_repository = PersistenceLayerRepositoryImplementation()

    def create_channel(self) -> SSEChannel:
        channel = SSEChannel()
        self.__channels_repository.persist(channel)
        return channel

    def subscribe(self, channel_id: str) -> str:
        channel = self.__channels_repository.load_one(channel_id)
        l = channel.add_listener()
        self.__channels_repository.persist(channel)
        return l.id

    def broadcast(self, target_channel_id: str, message_type: str):
        self.__channels_repository.load_one(target_channel_id).broadcast(Message(msg_type=message_type))


async def process_subscriber_messages(subscriber_id: str):
    listener = my_channel.get_listener(subscriber_id)
    listener.start()
    async for message in my_channel.message_stream(listener):
        print(f'Message: {message["event"]}')
        if message["event"] == 'stop':
            listener.stop()
            break

# Service bootstrap.
app = Application()

# Clients interaction

## Some client creates a channel
my_channel = app.create_channel()

## Later on, some other client makes a subscription
my_subscriber_id = app.subscribe(my_channel.id)

app.broadcast(my_channel.id, 'test')
app.broadcast(my_channel.id, 'stop')

# Subscriber starts a connection
if __name__ == '__main__':
    run(process_subscriber_messages(my_subscriber_id))


