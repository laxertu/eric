"""
A demo of full in memory usage of library
"""

import asyncio

from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel

channel = SSEChannel()
listener = channel.add_listener()

channel.dispatch(listener.id, Message(msg_type='test1', msg_payload='hi there'))
channel.dispatch(listener.id, Message(msg_type='test2', msg_payload='hi there!'))
channel.dispatch(listener.id, Message(msg_type='test3', msg_payload='hi there!!'))
listener.start()

async def main():
    input('Starting Press Enter to start stream and Ctrl+C to stop')

    try:
        async for sse_event in channel.message_stream(listener):
            print(f'Received message: {sse_event}')
    except KeyboardInterrupt:
        exit(0)

if __name__ == '__main__':

    asyncio.run(main())


