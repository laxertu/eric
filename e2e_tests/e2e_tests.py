import asyncio
from asyncio import run

from eric_sse.servers import SocketServer
from eric_sse.clients import SocketClient

SOCKET_FILE_DESCRIPTOR_PATH = 'socketserver_e2e_test.sock'
client = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)


async def say_hello():
    return await client.send_payload({
        'v': 'b',
        'c': '1',
        't': 'txt',
        'p': 'Hi there!'
    })


async def do_test():
    server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
    asyncio.get_running_loop().create_task(server.main())
    await asyncio.sleep(0)

    channel_id = await client.create_channel()
    assert channel_id == '1'

    listener_id = await client.register(channel_id=channel_id)
    assert listener_id == '1'

    server_response = await say_hello()
    assert server_response == SocketServer.ACK
    await server.shutdown()


def main():
    run(do_test())


if __name__ == "__main__":
    main()
