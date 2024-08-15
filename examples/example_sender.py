import asyncio, sys
from pathlib import Path

from examples import SOCKET_FILE_DESCIPTOR_PATH

CHUNK_SIZE = 100
async def main():
    try:
        r, w = await asyncio.open_unix_connection(Path(SOCKET_FILE_DESCIPTOR_PATH))
        w.write(sys.argv[1].encode())
        w.write_eof()

        response = await r.read()
        print(response.decode())

        # Close
        await w.drain()
        #w.write_eof()
        w.close()
        await w.wait_closed()
        print("message sent")




    except Exception as e:
        print(e)

asyncio.get_event_loop().run_until_complete(main())
