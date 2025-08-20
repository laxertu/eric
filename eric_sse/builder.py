from eric_sse.interfaces import ChannelRepositoryInterface, ConnectionRepositoryInterface

class ChannelBuilder:

    def __init__(self,
                 channel_repository: ChannelRepositoryInterface,
                 connection_repository: ConnectionRepositoryInterface,
                 ):
        self.channel_repository = channel_repository
        self.connection_repository = connection_repository

        def build_one(channel_id: str):
            channel = self.channel_repository.load_one(channel_id)
            for connection in self.connection_repository.load_all(channel_id):
                channel.register_connection(connection.listener, connection.queue)
