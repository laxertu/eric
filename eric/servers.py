import asyncio
import signal

from asyncio import StreamReader, StreamWriter, start_unix_server
from asyncio.exceptions import CancelledError
from pathlib import Path

import eric
from eric.model import Message
from eric.listeners import MessageQueueListener
from eric.eric import Eric
from eric.model import create_simple_mesage, InvalidChannelException

logger = eric.get_logger()

class SimpleServerListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        SimpleServer.eric.get_channel('main').broadcast(msg)

    def close(self) -> None:
        pass


class SimpleServer:
    eric = Eric()
    __main_listener = SimpleServerListener()

    def __init__(self, file_descriptor_path: str):
        self.__file_descriptor_path = file_descriptor_path
        self.eric = Eric()

    @staticmethod
    async def __prepare():
        try:
            SimpleServer.eric.get_channel('main')
        except InvalidChannelException:
            try:
                SimpleServer.eric.register_channel('main')
                SimpleServer.eric.get_channel('main').register_listener(SimpleServer.__main_listener)
                await SimpleServer.__main_listener.start()
            except Exception as e:
                print(e)

    @staticmethod
    def __process_message(msg: Message):
        ...

    @staticmethod
    async def connect_callback(reader: StreamReader, writer: StreamWriter):
        await SimpleServer.__prepare()
        message_content = await reader.read()
        message = create_simple_mesage(message_content.decode())

        SimpleServer.eric.get_channel('main').dispatch(SimpleServer.__main_listener, message)
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
        server = await start_unix_server(SimpleServer.connect_callback, path=Path(self.__file_descriptor_path))
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
            server = SimpleServer(file_descriptor_path)
            asyncio.run(server.main())
        except CancelledError:
            exit(0)

