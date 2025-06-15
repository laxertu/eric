import asyncio, logging

from eric_sse.message import Message, MessageContract
from eric_sse.prefabs import SimpleDistributedApplicationListener, SSEChannel

import  eric_sse
logger  = eric_sse.get_logger()

ssc = SSEChannel()

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

def create_listener(ch: SSEChannel):
    """
    Creates and starts a distributed application listener with predefined message handlers.
    
    The listener is configured to handle 'hello', 'hello_ack', and 'bye' message types using their respective handler functions, and is started synchronously on the provided SSE channel.
    
    Args:
        ch: The SSEChannel to bind the listener to.
    
    Returns:
        The initialized and started SimpleDistributedApplicationListener instance.
    """
    l = SimpleDistributedApplicationListener(ch)
    l.set_action('hello', hello_response)
    l.set_action('hello_ack', hello_ack_response)
    l.set_action('bye', bye_handler)
    l.start_sync()
    return l

async def do_stuff(buddy: SimpleDistributedApplicationListener):
    """
    Consumes messages from the global SSE channel for the specified listener.
    
    This coroutine asynchronously iterates over the message stream associated with
    the given listener, effectively draining incoming messages without processing
    them.
    """
    async for _ in ssc.message_stream(buddy):
        ...


async def main():

    """
    Sets up two distributed listeners and facilitates a message exchange between them.
    
    Creates two listeners on a shared SSE channel, initiates a 'hello' message from one to the other, and concurrently runs asynchronous tasks to process incoming messages for both listeners until completion.
    """
    alice = create_listener(ssc)
    bob = create_listener(ssc)

    # Bob says hello to Alice
    bob.dispatch_to(alice, Message(msg_type='hello', msg_payload='hello!'))

    f2 = asyncio.create_task(do_stuff(alice))
    f1 = asyncio.create_task(do_stuff(bob))

    await f1
    await f2

asyncio.run(main())
