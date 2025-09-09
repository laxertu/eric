Reference
=========

**Introduction**

If you just want a simple, inmemory SSE service, base building blocks are already available.

The following code creates a Server Side Events channel and attaches a listener to it.
`Here <https://github.com/laxertu/eric/blob/master/examples/inmemory.py>`_ is the complete example.

.. code-block:: python

    from eric_sse.message import Message
    from eric_sse.prefabs import SSEChannel

    channel = SSEChannel()
    listener = channel.add_listener()
    listener.start()
    channel.dispatch(listener.id, Message(msg_type='welcome', msg_payload='Hello!'))

    async def main():
        async for sse_event in channel.message_stream(listener):
            print(f'Received message: {sse_event}')

    if __name__ == '__main__':
        asyncio.run(main())

**Overview**

.. image:: _static/overview.png
   :scale: 50 %


| thanks a lot https://excalidraw.com !!

**What is this?**

Eric is basically a toolkit for building async message management applications, paying special attention to Server Side Events based ones.
Its main components are:

* A core model with a set of abstractions and prefabs that give support to SSE and more.
* A persistence layer composed by a set of interfaces and base classes for building concrete layers

:class:`~eric_sse.connection.ConnectionsFactory` is shared between components. Persistence uses it to create objects after data fetch, while channels create connections when receiving new subscriptions.


**Prefabs**

* :class:`~eric_sse.prefabs.SSEChannel` Server side Events support
* :class:`~eric_sse.prefabs.DataProcessingChannel` Launches parallel tasks when consuming queues and dispatches results to client who pushed them
* :class:`~eric_sse.prefabs.SimpleDistributedApplicationChannel` Acts like a Mediator between listeners that communicate each other




.. toctree::
   :maxdepth: 2
   :hidden:

   entities
   prefabs
   persistence
   exceptions


