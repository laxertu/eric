import asyncio

from eric_sse.entities import Message
from eric_sse.prefabs import SimpleDistributedApplicationListener, SSEChannel


def hello_response(m: Message) -> Message:
    return Message(type='hello', payload=f'{m.payload["payload"]}!')


def stop(m: Message) -> Message:
    pass


def create_listener(ssc: SSEChannel):
    l = SimpleDistributedApplicationListener(ssc)
    l.set_action('hello', hello_response)
    return l


async def main():
    ssc = SSEChannel()

    alice = create_listener(ssc)
    bob = create_listener(ssc)

    ssc.dispatch(alice.id, Message(type='hello', payload={'sender_id': bob.id, 'payload': 'hello!'}))
    ssc.dispatch(alice.id, Message(type='stop'))

    await bob.start()
    await alice.start()

    print("Alice's queue")
    async for m in await ssc.message_stream(alice):
        print(f'output {m}')
    ssc.dispatch(bob.id, Message(type='stop'))


    print("Bob's queue")
    async for m in await ssc.message_stream(bob):
        print(f'output {m}')


asyncio.get_event_loop().run_until_complete(main())
