import asyncio
import json
import signal

from asyncio import StreamReader, StreamWriter, start_unix_server
from asyncio.exceptions import CancelledError
from os import linesep
from pathlib import Path
from typing import AsyncIterable, Iterable

from eric_sse import get_logger
from eric_sse.entities import AbstractChannel
from eric_sse.message import MessageContract, Message
from eric_sse.exception import InvalidChannelException, InvalidMessageFormat
from eric_sse.prefabs import SSEChannel

logger = get_logger()


class ChannelContainer:
    """Helper class for management of multiple channels cases of use."""

    def __init__(self):
        self.__channels: dict[str: AbstractChannel] = {}


    def register(self, channel: AbstractChannel) -> None:
        if channel.id in self.__channels:
            raise InvalidChannelException(f'Channel with id {channel.id} already exists')
        self.__channels[channel.id] = channel

    def register_iterable(self, channels: Iterable[AbstractChannel]) -> None:
        registered_ids = set(self.get_all_ids())

        for channel in [c for c in channels if c.id not in registered_ids]:
            self.register(channel)

    def get(self, channel_id: str) -> AbstractChannel:
        try:
            return self.__channels[channel_id]
        except KeyError:
            raise InvalidChannelException(f'No channel with id {channel_id}')

    def rm(self, channel_id: str):
        try:
            del self.__channels[channel_id]
        except KeyError:
            raise InvalidChannelException(f'No channel with id {channel_id}')

    def get_all_ids(self) -> Iterable[str]:
        return self.__channels.keys()


class SocketServer:
    """
    An implementation of a socket server that acts as a controller to interact with library

    **Accepted format**: a plain JSON with the following keys::

        {        
            "c": "channel id" 
            "v": "verb" 
            "t": "message type" 
            "p": "message payload" 
            "r": "receiver (listener id when verb is 'rl')"
        }


    Possible values of **verb** identifies a supported action::

        "d" dispatch
        "b" broadcast
        "c" create channel
        "r" add listener
        "l" listen (opens a stream)
        "w" watch (opens a stream)
        "rl" remove a listener
        "rc" remove a channel

    See examples
    """
    cc = ChannelContainer()
    ACK = 'ack'

    def __init__(self, file_descriptor_path: str):
        """
        :param file_descriptor_path: See **start** method
        """
        self.__file_descriptor_path = file_descriptor_path
        self.__unix_server: asyncio.Server | None = None


    @staticmethod
    def start(file_descriptor_path: str):
        """
        Shortcut to start a server given a file descriptor path

        :param file_descriptor_path: file descriptor path, all understood by `Path <https://docs.python.org/3/library/pathlib.html#pathlib.Path>`_ is fine
        """
        logger.info('starting')
        try:
            server = SocketServer(file_descriptor_path)
            asyncio.run(server.main())
        except CancelledError:
            exit(0)

    @staticmethod
    def __parse(json_raw: str) -> (str, str, MessageContract | None, str):
        try:
            parsed = json.loads(json_raw)
            verb = parsed['v']

            channel_id = parsed.get('c')
            message = None
            if verb not in ['w', 'c', 'l', 'r', 'rl', 'rc']:
                message = Message(msg_type=parsed['t'], msg_payload=parsed.get('p'))

            receiver_id: str = parsed.get('r')
            return channel_id, verb, message, receiver_id

        except KeyError as e:
            logger.error(repr(e))
            raise InvalidMessageFormat(json_raw)

    @staticmethod
    async def connect_callback(reader: StreamReader, writer: StreamWriter):
        try:
            message_content = await reader.read()
            async for response in SocketServer.handle_command(message_content.decode()):
                writer.write(response.encode())
            writer.write_eof()
            await writer.drain()

        except Exception as e:
            logger.error(e)
            writer.write(repr(e).encode())
            writer.write_eof()
            await writer.drain()

    @staticmethod
    async def handle_command(raw_command: str) -> AsyncIterable[str]:
        channel_id, verb, message, receiver_id = SocketServer.__parse(raw_command)

        logger.info(f'received command {verb}')

        if verb == 'd':
            SocketServer.cc.get(channel_id).dispatch(receiver_id, message)
            yield SocketServer.ACK

        elif verb == 'c':
            channel = SSEChannel()
            SocketServer.cc.register(channel)
            yield channel.id

        elif verb == 'b':
            SocketServer.cc.get(channel_id).broadcast(message)
            yield SocketServer.ACK

        elif verb == 'r':
            l = SocketServer.cc.get(channel_id).add_listener()
            yield l.id

        elif verb == 'rl':
            SocketServer.cc.get(channel_id).remove_listener(listener_id=receiver_id)
            yield SocketServer.ACK

        elif verb == 'rc':
            SocketServer.cc.rm(channel_id)
            yield SocketServer.ACK

        elif verb == 'l':
            logger.info(f"Started listener {receiver_id} on {channel_id}")
            channel = SocketServer.cc.get(channel_id)
            listener = channel.get_listener(receiver_id)
            listener.start()
            async for m in channel.message_stream(listener):
                yield f'{json.dumps(m)}{linesep}'

        elif verb == 'w':
            logger.info(f"Client watching channel {channel_id}")
            channel = SocketServer.cc.get(channel_id)
            async for m in await channel.watch():
                yield f'{json.dumps(m)}{linesep}'

    async def shutdown(self):
        """Graceful Shutdown"""
        server = self.__unix_server
        logger.info("graceful shutdown")
        server.close()
        await server.wait_closed()
        Path(self.__file_descriptor_path).unlink()
        logger.info("done")

    async def main(self):
        """Starts the server"""
        server = await start_unix_server(SocketServer.connect_callback, path=Path(self.__file_descriptor_path))
        self.__unix_server = server
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            for sig in (signal.SIGINT, signal.SIGTERM):
                server.get_loop().add_signal_handler(sig, lambda: asyncio.ensure_future(self.shutdown()))
            await server.serve_forever()

