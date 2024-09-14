from eric.model import MessageQueueListener, Message

class LocalHostMessageQueueListener(MessageQueueListener):

    def close(self) -> None:
        ...

    def on_message(self, msg: Message) -> None:
        pass


