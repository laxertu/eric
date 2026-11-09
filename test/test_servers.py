import asyncio
import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase

from eric_sse.builder import ChannelRepositoryBuilder
from eric_sse.clients import SocketClient
from eric_sse.exception import InvalidChannelException, InvalidConnectionException, NoMessagesException
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.servers import SocketServer, ChannelContainer

SOCKET_FILE_DESCRIPTOR_PATH = 'socketserver_e2e_test.sock'


def create_channel() -> SSEChannel:
    return ChannelRepositoryBuilder(SSEChannel).build().create({})


class ChannelContainerTestCase(TestCase):

    def test_unknown_channels_can_be_neither_fetched_nor_removed(self):
        sut = ChannelContainer()

        with self.assertRaises(InvalidChannelException):
            sut.get('unknown')
        with self.assertRaises(InvalidChannelException):
            sut.rm('unknown')

    def test_registered_channels_can_be_fetched_and_listed(self):
        sut = ChannelContainer()
        channel = create_channel()

        sut.register(channel)

        self.assertIs(channel, sut.get(channel.id))
        self.assertEqual([channel.id], list(sut.get_all_ids()))

    def test_a_channel_cannot_be_registered_twice(self):
        sut = ChannelContainer()
        channel = create_channel()
        sut.register(channel)

        with self.assertRaises(InvalidChannelException):
            sut.register(channel)

    def test_registering_many_channels_skips_the_ones_already_registered(self):
        sut = ChannelContainer()
        registered, new = create_channel(), create_channel()
        sut.register(registered)

        sut.register_iterable([registered, new])

        self.assertCountEqual([registered.id, new.id], sut.get_all_ids())


class SocketServerTestCase(IsolatedAsyncioTestCase):
    """Commands sent through a real socket, on channels built by a repository."""

    async def asyncSetUp(self):
        SocketServer.cc = ChannelContainer()
        self.channel = create_channel()
        SocketServer.cc.register(self.channel)

        self.server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
        self.server_task = asyncio.create_task(self.server.main())
        while not Path(SOCKET_FILE_DESCRIPTOR_PATH).exists():
            await asyncio.sleep(0)
        self.client = SocketClient(SOCKET_FILE_DESCRIPTOR_PATH)

    async def asyncTearDown(self):
        await self.server.shutdown()
        await asyncio.gather(self.server_task, return_exceptions=True)
        SocketServer.cc = ChannelContainer()

    def _subscribe(self):
        connection = self.channel.add_connection()
        connection.listener.start()
        return connection

    async def test_created_channel_accepts_connections(self):
        channel_id = await self.client.create_channel()

        connection_id = await self.client.register(channel_id)

        self.assertEqual(connection_id, SocketServer.cc.get(channel_id).get_connection(connection_id).id)

    async def test_broadcast_reaches_every_connection(self):
        first, second = self._subscribe(), self._subscribe()

        response = await self.client.broadcast_message(self.channel.id, message_type='txt', payload='Hi there!')

        self.assertEqual(SocketServer.ACK, response)
        for connection in (first, second):
            message = self.channel.deliver_next(connection.id)
            self.assertEqual(('txt', 'Hi there!'), (message.type, message.payload))

    async def test_dispatch_reaches_only_the_receiver(self):
        receiver, other = self._subscribe(), self._subscribe()

        response = await self.client.dispatch(self.channel.id, receiver.id, message_type='txt', payload={'a': 1})

        self.assertEqual(SocketServer.ACK, response)
        self.assertEqual({'a': 1}, self.channel.deliver_next(receiver.id).payload)
        with self.assertRaises(NoMessagesException):
            self.channel.deliver_next(other.id)

    async def test_removed_connection_no_longer_receives_messages(self):
        connection_id = await self.client.register(self.channel.id)

        response = await self.client.remove_connection(self.channel.id, connection_id)

        self.assertEqual(SocketServer.ACK, response)
        with self.assertRaises(InvalidConnectionException):
            self.channel.get_connection(connection_id)
        error = await self.client.dispatch(self.channel.id, connection_id, message_type='txt', payload={})
        self.assertIn('InvalidConnectionException', error)

    async def test_removed_channel_no_longer_accepts_commands(self):
        response = await self.client.remove_channel(self.channel.id)

        self.assertEqual(SocketServer.ACK, response)
        error = await self.client.broadcast_message(self.channel.id, message_type='txt', payload={})
        self.assertIn('InvalidChannelException', error)

    async def test_commands_on_unknown_channels_get_an_error(self):
        error = await self.client.register('unknown')

        self.assertIn('InvalidChannelException', error)

    async def test_client_receives_messages_of_its_connection_as_a_stream(self):
        self.channel.wait_timeout_seconds = 0.01
        connection = self.channel.add_connection()
        self.channel.dispatch(connection.id, Message(msg_type='txt', msg_payload='Hi there!'))

        events = []

        async def consume():
            async for line in self.client.stream(self.channel.id, connection.id):
                if line:
                    events.append(json.loads(line))
                    connection.listener.stop()

        await asyncio.wait_for(consume(), timeout=2)

        self.assertEqual([('txt', 'Hi there!')], [(event['event'], event['data']) for event in events])
