import json, asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from eric_sse.clients import SocketClient
from eric_sse.prefabs import SSEChannel
from eric_sse.servers import SocketServer, SSEChannelContainer
SOCKET_FILE_DESCRIPTOR_PATH = 'socketserver_e2e_test.sock'


class SocketServerTestCase(IsolatedAsyncioTestCase):

    def setUp(self):
        channel_container_mock = MagicMock(SSEChannelContainer)
        channel_mock = MagicMock(SSEChannel)
        channel_container_mock.get = MagicMock(return_value=channel_mock)
        SocketServer.cc = channel_container_mock

        self.sut = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        self.channel_mock = channel_mock

    async def test_server(self):

        client = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)
        server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        asyncio.get_running_loop().create_task(server.main())
        await asyncio.sleep(0)


        server_response = await client.send_payload({
            'v': 'b',
            'c': '1',
            't': 'txt',
            'p': 'Hi there!'
        })

        self.assertEqual(server_response, SocketServer.ACK)
        await server.shutdown()

class SocketServerIntgrationTestCase(IsolatedAsyncioTestCase):

    def setUp(self):
        channel_container_mock = MagicMock(SSEChannelContainer)
        channel_mock = MagicMock(SSEChannel)
        channel_container_mock.get = MagicMock(return_value=channel_mock)
        SocketServer.cc = channel_container_mock

        self.sut = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        self.channel_mock = channel_mock

    async def test_send(self):
        payload = json.dumps({
            'c': '1',
            'v': 'b',
            't': 'txt',
            'p': 'Hi there!'
        })

        async for _ in self.sut.handle_command(payload):
            ...

        self.channel_mock.broadcast.assert_called_once()

