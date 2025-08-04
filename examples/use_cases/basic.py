"""
The simplest possible use of the library. Here unique dependency with persistence module is ChannelRepositoryInterface.
The rest of participants are from classed shipped from the library.

The following is a fake application with a in memory channel repository that just support channel creation and broadcasting
"""
from asyncio import run
from typing import Iterable

from eric_sse.entities import AbstractChannel
from eric_sse.prefabs import SSEChannel
from eric_sse.message import Message
from eric_sse.servers import ChannelContainer

from eric_sse.persistence import ChannelRepositoryInterface

class FakeChannelRepo(ChannelRepositoryInterface):
    """Fake repository"""

    def __init__(self):
        self.__channel_container = ChannelContainer()
        self.__channel_container.register(SSEChannel())
        self.__channel_container.register(SSEChannel())


    def delete_listener(self, ch_id: str, listener_id: str) -> None:
        self.__channel_container.get(ch_id).remove_listener(listener_id)

    def load(self) -> Iterable[AbstractChannel]:
        for c in self.__channel_container.get_all_ids():
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

def subscribe(ch_id: str) -> str:
    l = channel_container.get(ch_id).add_listener()
    return l.id

def broadcast(target_channel_id: str, message_type: str):
    channel_container.get(target_channel_id).broadcast(Message(msg_type=message_type))

# Clients interaction
channel_id = create_channel()
subscriber_id = subscribe(channel_id)

broadcast(channel_id, 'test')
broadcast(channel_id, 'stop')


async def main():
    print(f"Starting streaming for all channels and listeners, we expect some output from {channel_id}")
    print("")
    for ch_id in channel_container.get_all_ids():
        channel = channel_container.get(ch_id)
        print(f'Streaming channel {ch_id}')
        for l_id in channel.get_listeners_ids():
            listener = channel.get_listener(l_id)
            listener.start()
            async for message in channel.message_stream(listener):
                print(f'Message: {message["event"]}')
                if message["event"] == 'stop':
                    break
        print('done')
        print('')

if __name__ == '__main__':
    run(main())


