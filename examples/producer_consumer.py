import asyncio
from random import uniform
from time import sleep

from eric_sse import get_logger
from eric_sse.entities import Message, MessageQueueListener
from eric_sse.prefabs import DataProcessingChannel

logger = get_logger()


class Producer:

    @staticmethod
    def produce_num(c: DataProcessingChannel, l: MessageQueueListener, num: int):
        for i in range(0, num):
            c.dispatch(l.id, Message(type='counter', payload=i))
        c.notify_end()


class Consumer(MessageQueueListener):
    def on_message(self, msg: Message) -> None:
        sleep(uniform(0, 1))
        logger.info(f"Received {msg.type}: {msg.payload}")


async def main():
    # Here you can control message deliver frequency and max workers num
    channel = DataProcessingChannel(stream_delay_seconds=0, max_workers=6)
    listener = Consumer()
    channel.register_listener(listener)

    Producer.produce_num(c=channel, l=listener, num=20)

    await listener.start()
    async for msg in await channel.process_queue(listener):
        print(msg)


asyncio.get_event_loop().run_until_complete(main())
