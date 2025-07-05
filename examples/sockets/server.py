from asyncio import run, CancelledError

from eric_sse.listener import MessageQueueListener
from eric_sse.message import Message
from eric_sse.servers import SocketServer
from examples.sockets import SOCKET_FILE_DESCRIPTOR_PATH


class ExampleServerListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        super().on_message(msg)
        print(f"Received '{msg.payload}'")


async def main():
    server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
    channel = server.cc.add()

    print(f"Test an example delivery on an hello world with 'python sender.py {channel.id}'")
    await server.main()


if __name__ == '__main__':
    try:
        run(main())
    except CancelledError:
        exit(0)
