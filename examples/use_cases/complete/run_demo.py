import asyncio

from application import Application
from model import Forecast


async def main():
    a = Application()
    c = a.create_channel()
    l = a.subscribe(c)

    c.notify(Forecast(temperature=0.12))
    c.notify(Forecast(temperature=1.23))
    c.notify(Forecast(temperature=2.34))

    l.start()
    received = 0
    async for m in c.message_stream(l):
        print(m)
        received += 1
        if received == 3:
            break


if __name__ == '__main__':
    asyncio.run(main())