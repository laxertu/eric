"""
The simplest possible use of the library. Here unique dependency with persistence module is ChannelRepositoryInterface
"""
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.prefabs import SSEChannel
from eric_sse.message import Message
from eric_sse.servers import ChannelContainer

from eric_sse.persistence import ChannelRepositoryInterface


class FakeChannelRepo(ChannelRepositoryInterface):

    def __init__(self):
        self.__channel_container = ChannelContainer()


    def delete_listener(self, ch_id: str, listener_id: str) -> None:
        self.__channel_container.get(ch_id).remove_listener(listener_id)

    def load(self) -> Iterable[AbstractChannel]:
        for c in self.__channel_container.get_all_ids():
            print(c)
            yield self.__channel_container.get(c)

    def persist(self, persistable: SSEChannel):
        self.__channel_container.register(persistable)

    def delete(self, key: str):
        pass


# Service bootstrap.
channel_container = ChannelContainer()
channel_repository = FakeChannelRepo()
channel_container.register_iterable(channel_repository.load())

# Application controllers
def create_channel() -> str:
    channel = SSEChannel()

    # Add to real-time service
    channel_container.register(channel)
    # Save channel
    channel_repository.persist(channel)

    return channel.id

def broadcast(target_channel_id: str, message_type: str):
    channel_container.get(target_channel_id).broadcast(Message(msg_type=message_type))

# Client interaction
channel_id = create_channel()
broadcast(channel_id, 'test')







