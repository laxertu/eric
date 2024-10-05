import asyncio
import json
import os
import signal

from asyncio import StreamReader, StreamWriter, start_unix_server
from asyncio.exceptions import CancelledError
from pathlib import Path

import eric_sse
from eric_sse.entities import Message
from eric_sse.exception import InvalidChannelException, InvalidListenerException, InvalidMessageFormat
from eric_sse.prefabs import SSEChannel

logger = eric_sse.get_logger()


class ChannelContainer:
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

    A static shortcut for starting a basic server is provided. See examples.
    **Accepted format**: a plain (no nested) JSON with the following keys:

    ```
    "c": "channel id"
    "v": "verb"
    "t": "message type"
    "p": "message payload"
    ```


    Possible values of verb identifies a supported action:

    ```
    "d" dispatch
    "b" broadcast
    "c" add listener
    "w" watch (opens a stream)
    ```

    See examples
    """
    cc = ChannelContainer()

    def __init__(self, file_descriptor_path: str):
        self.__file_descriptor_path = file_descriptor_path

    @staticmethod
    def __parse(json_raw: str) -> (str, str, Message | None, str):
        try:
            parsed = json.loads(json_raw)
            channel_id = parsed['c']
            verb = parsed['v']
            message = None
            if verb not in ['w', 'c']:
                message = Message(type=parsed['t'], payload=parsed.get('p'))

            receiver_id: str = parsed.get('r')
            return channel_id, verb, message, receiver_id

        except KeyError as e:
            logger.error(repr(e))
            raise InvalidMessageFormat(json_raw)


    @staticmethod
    async def connect_callback(reader: StreamReader, writer: StreamWriter):
        """
        Integration with SocketServer.

        See https://docs.python.org/3/library/asyncio-stream.html#asyncio.start_unix_server
        Handles low-lwvel communication and raw messages parsing
        """
        try:
            message_content = await reader.read()
            channel_id, verb, message, receiver_id = SocketServer.__parse(message_content.decode())
            channel = SocketServer.cc.get(channel_id)

            logger.info(f'received command {verb}')

            if verb == 'd':
                channel.dispatch(receiver_id, message)
                writer.write('ack'.encode())
                writer.write_eof()
                await writer.drain()


            elif verb == 'b':
                channel.broadcast(message)
                writer.write('ack'.encode())
                writer.write_eof()
                await writer.drain()


            elif verb == 'c':
                l = channel.add_listener()
                writer.write(l.id.encode())
                writer.write_eof()
                await writer.drain()


            elif verb == 'w':
                logger.info(f"Client watching on listener {receiver_id}")
                async for m in await channel.message_stream(channel.get_listener(receiver_id)):
                    message = f'{json.dumps(m)}{os.linesep}'
                    logger.info(f"received message {message}")
                    writer.write(message.encode())

        except Exception as e:
                logger.error(e)
                writer.write(repr(e).encode())
                writer.write_eof()
                await writer.drain()

    async def shutdown(self, server: asyncio.Server):
        """Graceful Shutdown"""
        logger.info("graceful shutdown")
        server.close()
        await server.wait_closed()
        Path(self.__file_descriptor_path).unlink()
        logger.info("done")

    async def main(self):
        server = await start_unix_server(SocketServer.connect_callback, path=Path(self.__file_descriptor_path))
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            for sig in (signal.SIGINT, signal.SIGTERM):
                server.get_loop().add_signal_handler(
                    sig, lambda: asyncio.ensure_future(self.shutdown(server))
                )
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

