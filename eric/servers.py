import asyncio
import signal

from asyncio import StreamReader, StreamWriter, start_unix_server
from asyncio.exceptions import CancelledError
from pathlib import Path

import eric
from eric.model import Message
from eric.listeners import MessageQueueListener
from eric.model import create_simple_mesage, SSEChannel

logger = eric.get_logger()

class EricBroadCastListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        SocketServer.channel.broadcast(msg)

    def close(self) -> None:
        pass


class SocketServer:
    channel = SSEChannel()
    __main_listener = EricBroadCastListener()

    def __init__(self, file_descriptor_path: str):
        self.__file_descriptor_path = file_descriptor_path
        self.channel = SSEChannel()


    @staticmethod
    async def connect_callback(reader: StreamReader, writer: StreamWriter):
        message_content = await reader.read()
        message = create_simple_mesage(message_content.decode())

        SocketServer.channel.dispatch(SocketServer.__main_listener, message)
        writer.write('ack'.encode())
        writer.write_eof()
        await writer.drain()

    async def shutdown(self, server: asyncio.Server):
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
        logger.info('starting')
        try:
            server = SocketServer(file_descriptor_path)
            asyncio.run(server.main())
        except CancelledError:
            exit(0)

