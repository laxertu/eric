from asyncio import run, CancelledError

from eric_sse.entities import MessageQueueListener, Message
from eric_sse.servers import SocketServer
from examples.sockets import SOCKET_FILE_DESCRIPTOR_PATH


class ExampleServerListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        super().on_message(msg)
        print(f"Received '{msg.payload}'")


async def main():
    server = SocketServer(SOCKET_FILE_DESCRIPTOR_PATH)
    channel = server.cc.add()
    listener = ExampleServerListener()
    channel.register_listener(listener)

    listener2 = ExampleServerListener()
    channel.register_listener(listener2)

    print(f"Test an example delivery on an hello world with 'python example_sender.py {channel.id}'")
    print(f"Test SSE streaming with 'python example_watcher.py {channel.id} {listener.id}'")
    print(f"Test SSE streaming with 'python example_watcher.py {channel.id} {listener2.id}'")
    await listener.start()
    await listener2.start()
    await server.main()


if __name__ == '__main__':
    try:
        run(main())
    except CancelledError:
        exit(0)
