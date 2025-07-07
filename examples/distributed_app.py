import asyncio, logging

from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SimpleDistributedApplicationListener, SSEChannel

import  eric_sse
logger  = eric_sse.get_logger()


def output(m:MessageContract):
    print(m.payload)

def hello_response(m: MessageContract) -> list[Message]:
    output(m)
    return [
        Message(msg_type='hello_ack', msg_payload=f'{m.payload}!')
    ]

def hello_ack_response(m: MessageContract) -> list[Message]:
    output(m)
    try:
        next_message = input('Say something [CTRL-C to quit]: ')
    except KeyboardInterrupt:
        print("")
        print("Shutting down")
        return close_connection_response()

    return [Message(msg_type='hello', msg_payload=next_message)]

def close_connection_response() -> list[Message]:
    return [Message(msg_type='bye'), Message(msg_type='stop')]

def bye_handler(m: MessageContract) -> list[Message]:
    output(m)
    return close_connection_response()

async def create_listener(ch: SSEChannel):
    l = SimpleDistributedApplicationListener(ch)
    l.set_action('hello', hello_response)
    l.set_action('hello_ack', hello_ack_response)
    l.set_action('bye', bye_handler)
    l.start_sync()
    # TODO automatic register
    await ch.register_listener(l)
    return l

async def do_stuff(buddy: SimpleDistributedApplicationListener, ssc: SSEChannel):
    async for _ in ssc.message_stream(buddy):
        ...


async def main():
    ssc = SSEChannel()

    alice = await create_listener(ssc)
    bob = await create_listener(ssc)

    # Bob says hello to Alice
    await bob.dispatch_to(alice, Message(msg_type='hello', msg_payload='hello!'))

    f2 = asyncio.create_task(do_stuff(alice, ssc))
    f1 = asyncio.create_task(do_stuff(bob, ssc))

    await f1
    await f2

asyncio.run(main())
