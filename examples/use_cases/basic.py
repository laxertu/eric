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
        if channel.id in set(self.get_all_ids()):
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

class Application:
    def __init__(self):
        self.__persisted_channels_repository = FakeChannelRepo()
        self.__loaded_channels = ChannelContainer()

    def boot(self):
        self.__loaded_channels.register_iterable(self.__persisted_channels_repository.load())

    def create_channel(self) -> SSEChannel:
        channel = SSEChannel()

        # Add to real-time service
        self.__loaded_channels.register(channel)
        # Save channel
        self.__persisted_channels_repository.persist(channel)

        return channel

    def subscribe(self, channel: SSEChannel) -> str:
        l = channel.add_listener()
        return l.id

    def broadcast(self, target_channel_id: str, message_type: str):
        self.__loaded_channels.get(target_channel_id).broadcast(Message(msg_type=message_type))


async def process_subscriber_messages():
    listener = my_channel.get_listener(subscriber_id)
    listener.start()
    async for message in my_channel.message_stream(listener):
        print(f'Message: {message["event"]}')
        if message["event"] == 'stop':
            break

# Service bootstrap.
app = Application()
app.boot()

# Clients interaction
my_channel = app.create_channel()
subscriber_id = app.subscribe(my_channel)

app.broadcast(my_channel.id, 'test')
app.broadcast(my_channel.id, 'stop')


if __name__ == '__main__':
    run(process_subscriber_messages())


