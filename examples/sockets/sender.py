import asyncio
import json
import sys
from pathlib import Path

from examples.sockets import SOCKET_FILE_DESCRIPTOR_PATH


async def main():
    try:

        channel_id = sys.argv[1]

        r, w = await asyncio.open_unix_connection(Path(SOCKET_FILE_DESCRIPTOR_PATH))
        payload = {
            'c': channel_id,
            'v': 'b',
            't': 'txt',
            'p': 'Hi there!'
        }
        w.write(json.dumps(payload).encode())
        w.write_eof()

        response = await r.read()
        print(response.decode())

        # Close
        await w.drain()
        # w.write_eof()
        w.close()
        await w.wait_closed()
        print("message sent")

    except Exception as e:
        print(e)


asyncio.get_event_loop().run_until_complete(main())
