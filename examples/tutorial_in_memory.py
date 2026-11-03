"""
Tutorial: a complete in-memory application.

A chat room where users subscribe, receive private and broadcast messages, and leave.
Everything lives in the current process: no storage, no threads, no polling.

Run it with: python examples/tutorial_in_memory.py
"""
import asyncio

from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SSEChannel


# 1. A listener receives messages. Override on_message to react to each delivered message.
class ChatUser(MessageQueueListener):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def on_message(self, msg: MessageContract) -> None:
        # Leaving the room is just a message: stopping the listener ends its stream
        if msg.type == 'goodbye':
            self.stop()


# 2. A channel delivers messages to its listeners. Hooks let you customise it without touching its internals.
class ChatRoom(SSEChannel):

    def on_listener_added(self, listener: MessageQueueListener) -> None:
        print(f'[room] {listener.name} joined')

    def on_stream_end(self, listener: MessageQueueListener) -> None:
        print(f'[room] {listener.name} left')

    def before_dispatch(self, listener_id: str, msg: MessageContract) -> MessageContract | None:
        # Drop messages with forbidden words; returning None discards the message
        if 'spam' in str(msg.payload):
            return None
        return msg


async def user_session(room: ChatRoom, user: ChatUser):
    """What a web server does for each client: stream the channel's output for that listener."""
    # message_stream starts the listener, waits for messages without consuming CPU, and ends when the listener stops.
    # SSEChannel adapts every message to an SSE event: {'event': ..., 'retry': ..., 'data': ...}, plus 'id' if the message has one.
    # Errors become events of type 'error', see adapt_error.
    async for event in room.message_stream(user):
        print(f'[{user.name}] {event["event"]}: {event["data"]}')


async def main():
    room = ChatRoom()

    # 3. Subscribe: register existing listeners (add_listener() would create a plain MessageQueueListener instead)
    alice, bob = ChatUser('alice'), ChatUser('bob')
    room.register_listener(alice)
    room.register_listener(bob)

    # 4. Messages can be dispatched before streams start: they wait in each listener's queue
    room.dispatch(alice.id, Message(msg_type='private', msg_payload='hi alice, welcome!'))

    # 5. Stream to every user concurrently
    sessions = [asyncio.create_task(user_session(room, user)) for user in (alice, bob)]
    await asyncio.sleep(0.1)

    room.broadcast(Message(msg_type='chat', msg_payload='hello everybody'))
    room.broadcast(Message(msg_type='chat', msg_payload='buy spam now'))  # Dropped by before_dispatch
    await asyncio.sleep(0.1)

    # 6. Leave: each listener stops on its 'goodbye' message, its stream ends, and the listener is removed
    room.broadcast(Message(msg_type='goodbye'))
    await asyncio.gather(*sessions)
    for user in (alice, bob):
        room.remove_listener(user.id)


if __name__ == '__main__':
    asyncio.run(main())
