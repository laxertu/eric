import json
from pathlib import Path
from asyncio import open_unix_connection


class SocketClient:
    """
    A little facade to interact with SocketServer
    """
    def __init__(self, file_descriptor_path: str):
        self.__descriptor_path = Path(file_descriptor_path)

    async def send_payload(self, payload: dict):
        r, w = await open_unix_connection(self.__descriptor_path)
        w.write(json.dumps(payload).encode())
        w.write_eof()

        response = await r.read()
        await w.drain()
        w.close()
        await w.wait_closed()
        return response.decode()

    async def create_channel(self):
        return await self.send_payload({
            'v': 'c',
        })

    async def register(self, channel_id: str):
        return await self.send_payload({
            'v': 'r',
            'c': channel_id,
        })

    async def broadcast_message(self, channel_id: str, message_type: str, payload: str | dict | int | float):
        return await self.send_payload({
            'v': 'b',
            'c': channel_id,
            't': message_type,
            'p': payload
        })
