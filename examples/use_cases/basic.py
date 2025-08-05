"""
The simplest possible use of the persistence layer. Here unique dependency with it is with ChannelRepositoryInterface.
The rest of participants are from classes shipped from the library.

The following is a fake application with an in memory channel repository, and that just support channel creation and broadcasting
"""
from asyncio import run
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.prefabs import SSEChannel
from eric_sse.message import Message
from eric_sse.servers import ChannelContainer

from eric_sse.persistence import ChannelRepositoryInterface

class Cache(ChannelContainer):
    def update(self, channel: SSEChannel):
        if channel.id in self.get_all_ids():
            self.rm(channel.id)
        self.register(channel)

class FakeChannelRepo(ChannelRepositoryInterface):
    """Fake repository with two channels"""

    def __init__(self):
        self.__cache = Cache()
        self.persist(SSEChannel())
        self.persist(SSEChannel())

    def persist(self, persistable: SSEChannel):
        self.__cache.update(persistable)

    def load(self) -> Iterable[AbstractChannel]:
        for c in self.__cache.get_all_ids():
            yield self.__cache.get(c)

    def delete_listener(self, ch_id: str, listener_id: str) -> None:
        self.__cache.get(ch_id).remove_listener(listener_id)


    def delete(self, key: str):
        self.__cache.rm(key)

    def get_channel(self, channel_id: str) -> AbstractChannel:
        return self.__cache.get(channel_id)

class Application:
    def __init__(self):
        self.__channels_repository = FakeChannelRepo()

    def create_channel(self) -> SSEChannel:
        channel = SSEChannel()
        self.__channels_repository.persist(channel)
        return channel

    def subscribe(self, channel_id: str) -> str:
        channel = self.__channels_repository.get_channel(channel_id)
        l = channel.add_listener()
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

# Some client creates a channel
my_channel = app.create_channel()

# Later on, some other client makes a subscription
my_subscriber_id = app.subscribe(my_channel.id)

app.broadcast(my_channel.id, 'test')
app.broadcast(my_channel.id, 'stop')

# Subscriber starts a connection
if __name__ == '__main__':
    run(process_subscriber_messages(my_subscriber_id))


