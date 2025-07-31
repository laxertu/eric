from asyncio import run, CancelledError

from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.servers import SocketServer
from eric_sse.prefabs import SSEChannel
from examples.sockets import SOCKET_FILE_DESCRIPTOR_PATH

from eric_sse import get_logger

logger = get_logger()

class ExampleServerListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        super().on_message(msg)
        logger.info(f"Received '{msg.payload}'")


async def main():
    server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
    channel = SSEChannel()
    server.cc.register(channel)

    listener = ExampleServerListener()
    channel.register_listener(listener)

    print(f"Test an example delivery on an hello world with:")
    print("")
    print(f'python sender.py {channel.id}')
    print(f'python receiver.py {channel.id} {listener.id}')
    print("")
    await server.main()


if __name__ == '__main__':
    try:
        run(main())
    except CancelledError:
        exit(0)
