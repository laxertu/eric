import asyncio
from pathlib import Path
import json
from asyncio import run, open_unix_connection

from eric_sse.servers import SocketServer

SOCKET_FILE_DESCRIPTOR_PATH = 'socketserver_e2e_test.sock'

async def send_payload(payload: dict):
    r, w = await open_unix_connection(Path(SOCKET_FILE_DESCRIPTOR_PATH))
    w.write(json.dumps(payload).encode())
    w.write_eof()

    response = await r.read()
    await w.drain()
    w.close()
    await w.wait_closed()
    return response.decode()

async def create_channel():
    return await send_payload({
        'v': 'c',
    })

async def register():
    return await send_payload({
        'v': 'r',
        'c': '1',
    })

async def say_hello():
    return await send_payload({
        'v': 'b',
        'c': '1',
        't': 'txt',
        'p': 'Hi there!'
    })


async def do_test():
    server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
    asyncio.get_running_loop().create_task(server.main())
    await asyncio.sleep(0)

    channel_id = await create_channel()
    assert channel_id == '1'

    listener_id = await register()
    assert listener_id == '1'

    server_response = await say_hello()
    assert server_response == SocketServer.ACK
    await server.shutdown()

def main():
    print("Start E2E Test")
    run(do_test())

if __name__ == "__main__":
    main()

