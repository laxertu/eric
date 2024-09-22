from eric_sse import get_logger
import asyncio

logger = get_logger()

from eric_sse.entities import Message, MessageQueueListener, MESSAGE_TYPE_CLOSED
from eric_sse.prefabs import SSEChannel


class Producer:

    @staticmethod
    def produce_num(c: SSEChannel, l: MessageQueueListener, num: int):
        for i in range(1, num):
            c.dispatch(l.id, Message(type='counter', payload=i))
        c.dispatch(l.id, Message(type=MESSAGE_TYPE_CLOSED))

class Consumer(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        logger.info(f"Received {msg.type} {msg.payload}")
        if msg.type == MESSAGE_TYPE_CLOSED:
            logger.info(f"Stopping listener {self.id}")
            self.stop_sync()


async def main():

    # Here you can control message deliver frequency
    channel = SSEChannel(stream_delay_seconds=1)
    consumer = Consumer()
    channel.register_listener(consumer)
    Producer.produce_num(c=channel, l=consumer, num=10)

    await consumer.start()
    async for _ in await channel.message_stream(consumer):
        pass

asyncio.get_event_loop().run_until_complete(main())
