import asyncio
import json
import signal

from asyncio import StreamReader, StreamWriter, start_unix_server
from os import linesep
from pathlib import Path
from typing import AsyncIterable, Callable, Iterable

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
            "r": "receiver (connection id when verb is 'rl')"
        }


    Possible values of **verb** identifies a supported action::

        "d" dispatch
        "b" broadcast
        "c" create channel
        "r" add connection
        "l" listen (opens a stream)
        "w" watch (opens a stream)
        "rl" remove a connection
        "rc" remove a channel

    See examples
    """
    ACK = 'ack'

    def __init__(
            self,
            file_descriptor_path: str,
            channels: ChannelContainer | None = None,
            channel_factory: Callable[[], AbstractChannel] = SSEChannel
    ):
        """
        :param file_descriptor_path: See **start** method
        :param channels: the channels the server works on. A new empty container by default.
        :param channel_factory: creates the channels requested by the 'c' verb, e.g.
            ``lambda: repository.create({})`` for channels built by a repository. Creates plain SSEChannel by default.
        """
        self.cc = channels if channels is not None else ChannelContainer()
        self.__channel_factory = channel_factory
        self.__file_descriptor_path = file_descriptor_path
        self.__connections: set[asyncio.Task] = set()
        self.__stop_requested = asyncio.Event()
        self.__stopped = asyncio.Event()

    @staticmethod
    def start(file_descriptor_path: str):
        """
        Shortcut to start a server given a file descriptor path

        :param file_descriptor_path: file descriptor path, all understood by `Path <https://docs.python.org/3/library/pathlib.html#pathlib.Path>`_ is fine
        """
        logger.info('starting')
        asyncio.run(SocketServer(file_descriptor_path).main())

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

    async def connect_callback(self, reader: StreamReader, writer: StreamWriter):
        """
        Serves one client connection: runs its command, writes the responses and closes the connection.
        Tracked until it ends, so that shutdown can end open streams.
        """
        connection = asyncio.current_task()
        self.__connections.add(connection)
        try:
            message_content = await reader.read()
            async for response in self.handle_command(message_content.decode()):
                writer.write(response.encode())
            writer.write_eof()
            await writer.drain()

        except Exception as e:
            logger.error(e)
            writer.write(repr(e).encode())
            writer.write_eof()
            await writer.drain()

        finally:
            writer.close()
            self.__connections.discard(connection)

    async def handle_command(self, raw_command: str) -> AsyncIterable[str]:
        channel_id, verb, message, receiver_id = SocketServer.__parse(raw_command)

        logger.info(f'received command {verb}')

        if verb == 'd':
            self.cc.get(channel_id).dispatch(receiver_id, message)
            yield SocketServer.ACK

        elif verb == 'c':
            channel = self.__channel_factory()
            self.cc.register(channel)
            yield channel.id

        elif verb == 'b':
            self.cc.get(channel_id).broadcast(message)
            yield SocketServer.ACK

        elif verb == 'r':
            yield self.cc.get(channel_id).add_connection().id

        elif verb == 'rl':
            self.cc.get(channel_id).remove_connection(connection_id=receiver_id)
            yield SocketServer.ACK

        elif verb == 'rc':
            self.cc.rm(channel_id)
            yield SocketServer.ACK

        elif verb == 'l':
            logger.info(f"Started listener {receiver_id} on {channel_id}")
            channel = self.cc.get(channel_id)
            async for m in channel.message_stream(receiver_id):
                yield f'{json.dumps(m)}{linesep}'

        elif verb == 'w':
            logger.info(f"Client watching channel {channel_id}")
            channel = self.cc.get(channel_id)
            async for m in channel.watch():
                yield f'{json.dumps(m)}{linesep}'

    async def shutdown(self):
        """
        Graceful Shutdown: stops accepting connections, ends open streams and removes the socket file.
        Returns when done, and so does **main**. Same as sending SIGINT or SIGTERM to the process.
        """
        self.__stop_requested.set()
        await self.__stopped.wait()

    async def main(self):
        """Starts the server. Returns after a shutdown."""
        server = await start_unix_server(self.connect_callback, path=Path(self.__file_descriptor_path))
        logger.info(f'Serving on {server.sockets[0].getsockname()}')

        loop = asyncio.get_running_loop()
        signals = (signal.SIGINT, signal.SIGTERM)
        for sig in signals:
            loop.add_signal_handler(sig, self.__stop_requested.set)

        try:
            await self.__stop_requested.wait()
            logger.info("graceful shutdown")
            server.close()
            # Since Python 3.12 wait_closed() also waits for open connections: streams never end by themselves
            connections = list(self.__connections)
            for connection in connections:
                connection.cancel()
            await asyncio.gather(*connections, return_exceptions=True)
            await server.wait_closed()
            Path(self.__file_descriptor_path).unlink(missing_ok=True)
        finally:
            for sig in signals:
                loop.remove_signal_handler(sig)
            self.__stopped.set()
        logger.info("done")
