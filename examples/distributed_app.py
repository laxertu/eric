import asyncio, logging
from eric_sse.entities import Message
from eric_sse.prefabs import SimpleDistributedApplicationListener, SSEChannel
ssc = SSEChannel()

import  eric_sse
logger  = eric_sse.get_logger()
logger.setLevel(logging.DEBUG)


def hello_response(m: Message) -> list[Message]:
    return [
        Message(type='hello_ack', payload=f'{m.payload["payload"]}!'),
        Message(type='stop')
    ]

def hello_ack_response(m: Message) -> list[Message]:
    return [
        Message(type='stop')
    ]


def create_listener(ch: SSEChannel):
    l = SimpleDistributedApplicationListener(ch)
    l.set_action('hello', hello_response)
    l.set_action('hello_ack', hello_ack_response)
    l.start_sync()
    return l

async def do_stuff(buddy: SimpleDistributedApplicationListener):
    async for m in await ssc.message_stream(buddy):
        print(buddy.id, m)


async def main():

    alice = create_listener(ssc)
    bob = create_listener(ssc)

    # Bob says hello to Alice
    ssc.dispatch(alice.id, Message(type='hello', payload={'sender_id': bob.id, 'payload': 'hello!'}))

    f1 = asyncio.create_task(do_stuff(alice))
    f2 = asyncio.create_task(do_stuff(bob))

    await f1
    await f2

asyncio.get_event_loop().run_until_complete(main())
