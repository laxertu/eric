import asyncio
from random import uniform
from time import sleep
from eric_sse import get_logger
from eric_sse.entities import MessageQueueListener, MESSAGE_TYPE_CLOSED
from eric_sse.message import SignedMessage
from eric_sse.prefabs import DataProcessingChannel
from eric_redis_queues import RedisQueueFactory

logger = get_logger()


class Producer:

    @staticmethod
    def produce_num(c: DataProcessingChannel, l: MessageQueueListener, num: int):
        for i in range(0, num):
            c.dispatch(l.id, SignedMessage(msg_type='counter', msg_payload=i, sender_id='producer'))
        c.dispatch(l.id, SignedMessage(msg_type=MESSAGE_TYPE_CLOSED, sender_id='producer'))


class Consumer(MessageQueueListener):
    def on_message(self, msg: SignedMessage) -> None:
        sleep(uniform(0, 1))
        logger.info(f"Received {msg.type}: {msg.payload}")

class MyChannel(DataProcessingChannel):
    def set_f(self):
        self._set_queues_factory(RedisQueueFactory())
    def adapt(self, msg: SignedMessage) -> dict:
        return {'sender_id': msg.sender_id, 'payload': msg.payload}

async def main():
    # Here you can control message deliver frequency and max workers num
    channel = MyChannel(stream_delay_seconds=0, max_workers=6)
    channel.set_f()
    listener = Consumer()
    channel.register_listener(listener)

    Producer.produce_num(c=channel, l=listener, num=20)

    await listener.start()

    async for msg in await channel.process_queue(listener):
        print(msg)



asyncio.get_event_loop().run_until_complete(main())
