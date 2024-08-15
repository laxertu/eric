from examples import SOCKET_FILE_DESCIPTOR_PATH
from eric.servers import SocketServer

#e = Eric()
#c = e.register_channel('example_ch')
#l = c.add_listener(LocalHostMessageQueueListener)


if __name__ == '__main__':
    SocketServer.start(SOCKET_FILE_DESCIPTOR_PATH)
