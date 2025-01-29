import json
from pathlib import Path
from asyncio import open_unix_connection
from typing import AsyncIterable

class SocketClient:
    """
    A little facade to interact with SocketServer
    """

    def __init__(self, file_descriptor_path: str):
        self.__descriptor_path = Path(file_descriptor_path)

    async def send_payload(self, payload: dict):
        """
        Send an arbitrary payload to a socket

        see :class:`eric_sse.servers.SocketServer`
        """
        r, w = await open_unix_connection(self.__descriptor_path)
        w.write(json.dumps(payload).encode())
        w.write_eof()

        response = await r.read()
        await w.drain()
        w.close()
        await w.wait_closed()
        return response.decode()

    async def create_channel(self) -> str:
        return await self.send_payload({
            'v': 'c',
        })

    async def register(self, channel_id: str):
        return await self.send_payload({
            'v': 'r',
            'c': channel_id,
        })

    async def stream(self, channel_id, listener_id) -> AsyncIterable[str]:
        r, w = await open_unix_connection(self.__descriptor_path)
        payload = {
            'c': channel_id,
            'r': listener_id,
            'v': 'l',
        }
        w.write(json.dumps(payload).encode())
        w.write_eof()
        await w.drain()

        while not r.at_eof():
            m = await r.readline()
            yield m.decode()

    async def broadcast_message(self, channel_id: str, message_type: str, payload: str | dict | int | float):
        return await self.send_payload({
            'v': 'b',
            'c': channel_id,
            't': message_type,
            'p': payload
        })

    async def dispatch(self, channel_id: str, receiver_id: str, message_type: str, payload: str | dict | int | float):
        return await self.send_payload({
            'v': 'd',
            'c': channel_id,
            'r': receiver_id,
            't': message_type,
            'p': payload
        })

    async def remove_listener(self, channel_id: str, listener_id: str):
        return await self.send_payload({
            'v': 'rl',
            'c': channel_id,
            'r': listener_id
        }
        )

    async def remove_channel(self, channel_id: str):
        return await self.send_payload({
            'v': 'rc',
            'c': channel_id
        }
        )
