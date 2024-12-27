import asyncio
from websockets.asyncio.server import serve, ServerConnection
from dotenv import load_dotenv
import os

load_dotenv()

device_conn_to_in_conn: dict[ServerConnection, ServerConnection | None] = {}
id_to_device_conn: dict[str, ServerConnection] = {}

SPLIT = "#"


async def loop(conn: ServerConnection):
    async for message in conn:
        parts = message.split(SPLIT)
        if parts[0] == "available":
            id_conn = parts[1]
            id_to_device_conn[id_conn] = conn
            device_conn_to_in_conn[conn] = None
            await conn.send("complete")
        elif parts[0] == "connect":
            id_conn = parts[1]
            device_conn = id_to_device_conn[id_conn]
            if device_conn in device_conn_to_in_conn:
                device_conn_to_in_conn[device_conn] = conn
                await conn.send("connected")
                await device_conn.send("connected")
            else:
                await conn.send("unavailable")
        elif parts[0] == "disconnect":
            device_conn = [i[0] for i in device_conn_to_in_conn.items() if i[1] == conn][0]
            await device_conn.send("disconnected")
            await conn.send("complete")
            device_conn_to_in_conn[conn] = None
        elif parts[0] == "unavailable":
            in_conn = device_conn_to_in_conn[conn]
            id_conn = [i[0] for i in id_to_device_conn.items() if i[1] == conn][0]
            if in_conn is not None:
                await in_conn.send("disconnected")
            await conn.send("complete")
            del device_conn_to_in_conn[conn]
            del id_to_device_conn[id_conn]
        elif parts[0] == "control":
            device_id_conn = parts[1]
            device_conn = id_to_device_conn[device_id_conn]
            await device_conn.send(message)


async def main():
    host, port = os.getenv("host"), os.getenv("port")
    async with serve(loop, host, port) as server:
        print(f"Started ws://{host}:{port}")
        await server.serve_forever()


asyncio.run(main())
