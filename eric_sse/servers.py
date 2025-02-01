import asyncio
import json
import signal
from asyncio import StreamReader, StreamWriter, start_unix_server
from asyncio.exceptions import CancelledError
from os import linesep
from pathlib import Path
from typing import AsyncIterable

from eric_sse import get_logger
from eric_sse.message import MessageContract, Message
from eric_sse.exception import InvalidChannelException, InvalidListenerException, InvalidMessageFormat
from eric_sse.prefabs import SSEChannel

logger = get_logger()


class SSEChannelContainer:
    """Helper class for management of multiple SSE channels cases of use."""

    def __init__(self):
        self.__channels: dict[str: SSEChannel] = {}

    def add(self) -> SSEChannel:
        channel = SSEChannel()
        if channel.id in self.__channels:
            raise InvalidListenerException(f'Channel with id {channel.id} already exists')
        self.__channels[channel.id] = channel
        return channel

    def get(self, channel_id: str) -> SSEChannel:
        try:
            return self.__channels[channel_id]
        except KeyError:
            raise InvalidChannelException(f'No channel with id {channel_id}')

    def rm(self, channel_id: str):
        del self.__channels[channel_id]


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
    cc = SSEChannelContainer()
    ACK = 'ack'

    def __init__(self, file_descriptor_path: str):
        self.__file_descriptor_path = file_descriptor_path
        self.__unix_server: asyncio.Server | None = None

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
            channel = SocketServer.cc.add()
            yield channel.id

        elif verb == 'b':
            SocketServer.cc.get(channel_id).broadcast(message)
            yield SocketServer.ACK

        elif verb == 'r':
            l = SocketServer.cc.get(channel_id).add_listener()
            yield l.id

        elif verb == 'rl':
            SocketServer.cc.get(channel_id).remove_listener(l_id=receiver_id)
            yield SocketServer.ACK

        elif verb == 'rc':
            SocketServer.cc.rm(channel_id)
            yield SocketServer.ACK

        elif verb == 'l':
            logger.info(f"Client listening on {receiver_id}")
            channel = SocketServer.cc.get(channel_id)
            async for m in await channel.message_stream(channel.get_listener(receiver_id)):
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
        server = await start_unix_server(SocketServer.connect_callback, path=Path(self.__file_descriptor_path))
        self.__unix_server = server
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            for sig in (signal.SIGINT, signal.SIGTERM):
                server.get_loop().add_signal_handler(sig, lambda: asyncio.ensure_future(self.shutdown()))
            await server.serve_forever()

    @staticmethod
    def start(file_descriptor_path: str):
        """Shortcut to start a server"""
        logger.info('starting')
        try:
            server = SocketServer(file_descriptor_path)
            asyncio.run(server.main())
        except CancelledError:
            exit(0)
