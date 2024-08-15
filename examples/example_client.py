import asyncio
from pathlib import Path
async def main():
    try:
        r, w = await asyncio.open_unix_connection(Path(f"./sockets/example_ch.sock"))
    except Exception as e:
        print(e)
        raise e
    reader: asyncio.StreamReader = r

    raw = await reader.read()
    print(raw)

    #async for msg in await c.message_stream(l):
        #print(msg)

asyncio.run(main())