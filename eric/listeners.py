from eric.entities import MessageQueueListener, Message
from logging import Logger

class BackGroundLogger(MessageQueueListener):

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger

    def on_message(self, msg: Message) -> None:
        self.logger.log(level=int(msg.type), msg=msg.payload)
