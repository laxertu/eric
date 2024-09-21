from eric import get_logger
import asyncio

logger = get_logger()

from eric.entities import Message, MessageQueueListener, SSEChannel

class Producer:

    @staticmethod
    def produce_num(c: SSEChannel, l: MessageQueueListener, num: int):
        for i in range(1, num):
            c.dispatch(l.id, Message(type='counter', payload=i))

class Consumer(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        logger.info(f"Received {msg.type} {msg.payload}")


async def main():

    # Here you can control message deliver frequency
    channel = SSEChannel(stream_delay_seconds=1)
    consumer = Consumer()
    channel.register_listener(consumer)
    Producer.produce_num(c=channel, l=consumer, num=10)

    await consumer.start()
    async for msg in await channel.message_stream(consumer):
        if msg['data'] == 9:
            exit(0)

asyncio.get_event_loop().run_until_complete(main())
