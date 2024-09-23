from eric_sse import get_logger
import asyncio

logger = get_logger()

from eric_sse.entities import Message, MessageQueueListener, MESSAGE_TYPE_CLOSED
from eric_sse.prefabs import ThreadPoolListener, DataProcessingChannel


class Producer:

    @staticmethod
    def produce_num(c: DataProcessingChannel, l: MessageQueueListener, num: int):
        for i in range(1, num):
            c.dispatch(l.id, Message(type='counter', payload=i))
        c.dispatch(l.id, Message(type=MESSAGE_TYPE_CLOSED))

class Consumer(ThreadPoolListener):
    def __init__(self, max_workers: int):
        super().__init__(callback=self._on_message, max_workers=max_workers)

    @staticmethod
    def _on_message(msg: Message) -> None:
        logger.info(f"Received {msg.payload}: {msg.payload}")


async def main():

    # Here you can control message deliver frequency
    channel = DataProcessingChannel(stream_delay_seconds=0)
    # And max wprkers num
    consumer = Consumer(max_workers=10)
    channel.register_listener(consumer)
    Producer.produce_num(c=channel, l=consumer, num=20)

    await consumer.start()
    async for _ in await channel.message_stream(consumer):
        pass

asyncio.get_event_loop().run_until_complete(main())
