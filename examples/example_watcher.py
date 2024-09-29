import asyncio, sys
import json
from pathlib import Path

from examples import SOCKET_FILE_DESCRIPTOR_PATH


async def main():
    try:

        channel_id = sys.argv[1]
        receiver_id = sys.argv[2]

        r, w = await asyncio.open_unix_connection(Path(SOCKET_FILE_DESCRIPTOR_PATH))
        payload = {
            'c': channel_id,
            'r': receiver_id,
            'v': 'w',
        }
        w.write(json.dumps(payload).encode())
        w.write_eof()
        await w.drain()
        print('waiting...')

        while not r.at_eof():
            m = await r.readline()
            print(m.decode())

    except Exception as e:
        print(e)

asyncio.run(main())
