import json, asyncio
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import MagicMock

from eric_sse.clients import SocketClient
from eric_sse.exception import InvalidChannelException
from eric_sse.prefabs import SSEChannel
from eric_sse.servers import SocketServer, ChannelContainer
SOCKET_FILE_DESCRIPTOR_PATH = 'socketserver_e2e_test.sock'


class TestChannelContainer(TestCase):
    def test_exceptions(self):
        sut = ChannelContainer()

        with self.assertRaises(InvalidChannelException):
            sut.rm('fake_channel_id')

        with self.assertRaises(InvalidChannelException):
            sut.get('fake_channel_id')

class TestSocketServer(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        channel_container_mock = MagicMock(ChannelContainer)
        channel_mock = MagicMock(SSEChannel)
        channel_container_mock.get = MagicMock(return_value=channel_mock)
        SocketServer.cc = channel_container_mock

        self.sut = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        self.channel_mock = channel_mock

        asyncio.get_running_loop().create_task(self.sut.main())
        await asyncio.sleep(0)

    async def asyncTearDown(self):
        await self.sut.shutdown()
        SocketServer.cc = ChannelContainer()

class SocketServerTestCase(TestSocketServer):


    async def test_server(self):

        client = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)
        server_response = await client.send_payload({
            'v': 'b',
            'c': '1',
            't': 'txt',
            'p': 'Hi there!'
        })

        self.assertEqual(server_response, SocketServer.ACK)

class SocketServerIntegrationTestCase(TestSocketServer):


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


class ClientIntegrationTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        asyncio.get_running_loop().create_task(server.main())
        await asyncio.sleep(0)
        self.sut = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)
        self.server = server

    async def asyncTearDown(self):
        await self.server.shutdown()

    async def test_integration(self):

        channel_id = await self.sut.create_channel()
        self.assertEqual(len(channel_id), 36)

        listener_id = await self.sut.register(channel_id)
        self.assertEqual(len(listener_id), 36)

        error_message = await self.sut.register('2')
        self.assertTrue('InvalidChannelException' in error_message)

        response = await self.sut.broadcast_message(channel_id=channel_id, message_type='test', payload={})
        self.assertEqual(response, SocketServer.ACK)

        listener_id_2 = await self.sut.register(channel_id)
        response = await self.sut.dispatch(
            channel_id=channel_id, receiver_id=listener_id_2, message_type='test', payload={}
        )
        self.assertEqual(response, SocketServer.ACK)


        response = await self.sut.remove_listener(channel_id=channel_id, listener_id=listener_id_2)
        self.assertEqual(response, SocketServer.ACK)

        error_message = await self.sut.dispatch(
            channel_id=channel_id, receiver_id=listener_id_2, message_type='test', payload={}
        )
        self.assertTrue('InvalidListenerException' in error_message)

        response = await self.sut.remove_channel(channel_id=channel_id)
        self.assertEqual(response, SocketServer.ACK)

        error_message = await self.sut.broadcast_message(channel_id=channel_id, message_type='test', payload={})
        self.assertTrue('InvalidChannelException' in error_message)
