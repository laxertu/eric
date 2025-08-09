"""
The simplest possible use of the persistence layer. Here unique dependency with it is with ChannelRepositoryInterface.
The rest of participants are from classes shipped from the library.

The following is a fake application with an in memory channel repository, and that just support channel creation and broadcasting
"""
from asyncio import run
from typing import Iterable

from eric_sse.prefabs import SSEChannel
from eric_sse.message import Message
from eric_sse.persistence import ItemNotFound, ObjectAsKeyValuePersistenceMixin

from eric_sse.interfaces import ChannelRepositoryInterface, ConnectionRepositoryInterface
from eric_sse.serializable import ConnectionRepository
from eric_sse.inmemory import InMemoryStorage


class PersistenceLayerRepositoryImplementation(ChannelRepositoryInterface):
    """Fake repository"""

    def __init__(self):
        self.__channels: dict[str, SSEChannel] = {}
        self.__connection_repository = ConnectionRepository(InMemoryStorage())

    @property
    def connections_repository(self) -> ConnectionRepositoryInterface:
        return self.__connection_repository


    def persist(self, channel: SSEChannel):
        self.__channels[channel.id] = channel

    def load_one(self, channel_id: str) -> ObjectAsKeyValuePersistenceMixin:
        try:
            return self.__channels[channel_id]
        except KeyError:
            raise ItemNotFound(channel_id)

    def load_all(self) -> Iterable[SSEChannel]:
        for c in self.__channels.keys():
            yield self.__channels.get(c)

    def delete_listener(self, ch_id: str, listener_id: str) -> None:
        channel = self.__channels.get(ch_id)
        channel.remove_listener(listener_id)
        self.persist(channel)

    def delete(self, channel_id: str):
        del self.__channels[channel_id]

    def get_channel(self, channel_id: str) -> SSEChannel:
        return self.__channels.get(channel_id)

class Application:
    def __init__(self):
        self.__channels_repository = PersistenceLayerRepositoryImplementation()

    def create_channel(self) -> SSEChannel:
        channel = SSEChannel()
        self.__channels_repository.persist(channel)
        return channel

    def subscribe(self, channel_id: str) -> str:
        channel = self.__channels_repository.get_channel(channel_id)
        l = channel.add_listener()
        self.__channels_repository.persist(channel)
        return l.id

    def broadcast(self, target_channel_id: str, message_type: str):
        self.__channels_repository.get_channel(target_channel_id).broadcast(Message(msg_type=message_type))


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


