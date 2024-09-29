from eric_sse import get_logger
import asyncio

logger = get_logger()

from eric_sse.entities import Message, MessageQueueListener
from eric_sse.prefabs import DataProcessingChannel


class Producer:

    @staticmethod
    def produce_num(c: DataProcessingChannel, l: MessageQueueListener, num: int):
        for i in range(1, num):
            c.dispatch(l.id, Message(type='counter', payload=i))
        c.notify_end()

def on_message(msg: Message) -> None:
    logger.info(f"Received {msg.payload}: {msg.payload}")

async def main():

    # Here you can control message deliver frequency
    channel = DataProcessingChannel(stream_delay_seconds=0, max_workers=2)
    # And max wprkers num
    listener = channel.add_threaded_listener(callback=on_message)
    Producer.produce_num(c=channel, l=listener, num=21)

    await listener.start()
    async for _ in await channel.message_stream(listener):
        pass

asyncio.get_event_loop().run_until_complete(main())
