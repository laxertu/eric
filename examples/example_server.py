from examples import SOCKET_FILE_DESCIPTOR_PATH
from eric.servers import SocketServer

if __name__ == '__main__':
    SocketServer.start(SOCKET_FILE_DESCIPTOR_PATH)
