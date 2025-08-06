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
    print("Starting streamin press CTRL-C to quit")
    try:
        async for m in c.message_stream(l):
            print(m)
    except KeyboardInterrupt:
        exit(0)

if __name__ == '__main__':
    asyncio.run(main())