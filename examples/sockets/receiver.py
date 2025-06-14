import sys

import asyncio

from eric_sse.clients import SocketClient
from examples.sockets import SOCKET_FILE_DESCRIPTOR_PATH


async def main(channel_id):
    client = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)

    listener_id = await client.register(channel_id)
    async for m in client.stream(channel_id, listener_id):
        print(m)


if __name__ == '__main__':
    try:
        asyncio.run(main(sys.argv[1]))
    except IndexError:
        print(f'Usage: {sys.argv[0]} <channel_id>')
    except KeyboardInterrupt:
        print('bye')
        exit(0)


