import asyncio

from argparse import ArgumentParser
from random import uniform
from time import sleep
from eric_sse import get_logger
from eric_sse.entities import MESSAGE_TYPE_CLOSED
from eric_sse.listener import MessageQueueListener
from eric_sse.message import SignedMessage
from eric_sse.prefabs import DataProcessingChannel

# TODO support to these parameters
arguments_parser = ArgumentParser()
arguments_parser.add_argument('-b', choices=['r', 'i'], default='i', help='Backend to use. "r" = redis, "i" = in memory')
cli_arguments = arguments_parser.parse_args()

logger = get_logger()

class Producer:

    @staticmethod
    async def produce_num(c: DataProcessingChannel, l: MessageQueueListener, num: int):
        for i in range(0, num):
            c.dispatch(l.id, SignedMessage(msg_type='counter', msg_payload=i, sender_id='producer'))
        c.dispatch(l.id, SignedMessage(msg_type=MESSAGE_TYPE_CLOSED, sender_id='producer'))


class Consumer(MessageQueueListener):
    def on_message(self, msg: SignedMessage) -> None:
        sleep(uniform(0, 1))
        logger.info(f"Received {msg.type}: {msg.payload}")

class MyChannel(DataProcessingChannel):

    def adapt(self, msg: SignedMessage) -> dict:
        return {'sender_id': msg.sender_id, 'payload': msg.payload}

async def main():
    # Here you can control message deliver frequency and max workers num
    channel = MyChannel(stream_delay_seconds=0, max_workers=6)


    listener = Consumer()
    channel.register_listener(listener)

    await Producer.produce_num(c=channel, l=listener, num=20)

    listener.start()
    async for m in channel.process_queue(listener):
        print(m)

asyncio.run(main())
