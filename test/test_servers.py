import json

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from eric_sse.prefabs import SSEChannel
from eric_sse.servers import SocketServer, ChannelContainer


class SocketServerTestCase(IsolatedAsyncioTestCase):

    def setUp(self):
        channel_container_mock = MagicMock(ChannelContainer)
        channel_mock = MagicMock(SSEChannel)
        channel_container_mock.get = MagicMock(return_value=channel_mock)
        SocketServer.cc = channel_container_mock

        self.sut = SocketServer('')
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
