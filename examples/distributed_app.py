import asyncio, logging

from eric_sse.entities import Message
from eric_sse.prefabs import SimpleDistributedApplicationListener, SSEChannel

import  eric_sse
logger  = eric_sse.get_logger()
logger.setLevel(logging.ERROR)

ssc = SSEChannel()


def hello_response(m: Message) -> list[Message]:
    print(m)
    return [
        Message(type='hello_ack', payload=f'{m.payload["payload"]}!')
    ]

def hello_ack_response(m: Message) -> list[Message]:
    print(m)
    try:
        next_message = input('Say something: ')
    except KeyboardInterrupt:
        print("")
        print("Shutting down")
        return close_connection_response()

    return [Message(type='hello', payload=next_message)]

def close_connection_response() -> list[Message]:
    return [Message(type='bye'), Message(type='stop')]

def bye_handler(m: Message) -> list[Message]:
    print(m)
    return close_connection_response()

def create_listener(ch: SSEChannel):
    l = SimpleDistributedApplicationListener(ch)
    l.set_action('hello', hello_response)
    l.set_action('hello_ack', hello_ack_response)
    l.set_action('bye', bye_handler)
    l.start_sync()
    return l

async def do_stuff(buddy: SimpleDistributedApplicationListener):
    async for m in await ssc.message_stream(buddy):
        ...


async def main():

    alice = create_listener(ssc)
    bob = create_listener(ssc)

    # Bob says hello to Alice
    bob.dispatch_to(alice, Message(type='hello', payload='hello!'))

    try:
        f2 = asyncio.create_task(do_stuff(alice))
        f1 = asyncio.create_task(do_stuff(bob))

        await f1
        await f2
    except KeyboardInterrupt:
        print("Exiting...")
        alice.stop_sync()
        bob.stop_sync()


asyncio.get_event_loop().run_until_complete(main())
