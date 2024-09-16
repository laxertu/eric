from eric import get_logger

logger = get_logger()

from eric.entities import Message, MessageQueueListener, SSEChannel

class Producer:

    @staticmethod
    def produce_num(c: SSEChannel, l: MessageQueueListener, num: int):
        for i in range(1, num):
            c.dispatch(l, Message(type='counter', payload=i))

class Consumer(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        logger.info(f"Received {msg.type} {msg.payload}")


# Here you can control message deliver frequency
channel = SSEChannel(stream_delay_seconds=1)

consumer = channel.add_listener(Consumer)
Producer.produce_num(c=channel, l=consumer, num=10)
logger.info("Two Nones here")
logger.info(channel.deliver_next(consumer.id))
logger.info(channel.deliver_next(consumer.id))
logger.info("We have to start consumer")
consumer.start_sync()
logger.info(channel.deliver_next(consumer.id))
logger.info(channel.deliver_next(consumer.id))
