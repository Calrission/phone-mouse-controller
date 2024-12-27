import asyncio
from typing import Coroutine

from websockets import ConnectionClosed
from websockets.asyncio.server import serve, ServerConnection
from dotenv import load_dotenv
import os

load_dotenv()

device_conn_to_controller_conn: dict[ServerConnection, ServerConnection | None] = {}
id_to_device_conn: dict[str, ServerConnection] = {}

SPLIT = "#"


async def safe_send(conn: ServerConnection, msg: str) -> bool:
    try:
        await conn.send(msg)
        return True
    except ConnectionClosed:
        is_device = conn in device_conn_to_controller_conn
        is_controller = len([i[1] for i in device_conn_to_controller_conn.items() if i[1] == conn]) == 1
        if is_device:
            search_device_id = [i[0] for i in id_to_device_conn.items() if i[1] == conn]
            if len(search_device_id) != 0:
                device_id = search_device_id[0]
                del id_to_device_conn[device_id]
            if conn in device_conn_to_controller_conn:
                controller_connection = device_conn_to_controller_conn[conn]
                del device_conn_to_controller_conn[conn]
                await safe_send(controller_connection, "disconnected")
        elif is_controller:
            search_device_connection = [i[0] for i in device_conn_to_controller_conn.items() if i[1] == conn]
            if len(search_device_connection) != 0:
                device_connection = search_device_connection[0]
                del device_conn_to_controller_conn[device_connection]
                await safe_send(device_connection, "disconnected")
        return False


pings: dict[ServerConnection, Coroutine] = {}


async def loop(conn: ServerConnection):
    async for message in conn:
        parts = message.split(SPLIT)
        if parts[0] == "pong":
            if conn in pings:
                callback = pings[conn]
                del pings[conn]
                await callback
        if parts[0] == "available":
            id_conn = parts[1]
            id_to_device_conn[id_conn] = conn
            device_conn_to_controller_conn[conn] = None
            await safe_send(conn, "complete")
        elif parts[0] == "connect":
            id_conn = parts[1]
            device_conn = id_to_device_conn[id_conn]
            if device_conn in device_conn_to_controller_conn:
                if device_conn_to_controller_conn[device_conn] is None:
                    device_conn_to_controller_conn[device_conn] = conn
                    await safe_send(conn, "connected")
                    await safe_send(device_conn, "connected")
                else:
                    controller = device_conn_to_controller_conn[device_conn]
                    is_alive = await safe_send(controller, "ping")
                    try:
                        async def wrapped():
                            await safe_send(conn, "not connected")

                        if not is_alive:
                            raise asyncio.TimeoutError()
                        else:
                            pings[controller] = wrapped()
                            await asyncio.sleep(10)
                            raise asyncio.TimeoutError()
                    except asyncio.TimeoutError:
                        if is_alive:
                            await safe_send(device_conn, "disconnected")
                            await controller.close()
                        device_conn_to_controller_conn[device_conn] = conn
                        await safe_send(device_conn, "connected")
                        await safe_send(conn, "connected")
            else:
                await safe_send(conn, "unavailable")
        elif parts[0] == "disconnect":
            device_conn = [i[0] for i in device_conn_to_controller_conn.items() if i[1] == conn][0]
            await safe_send(device_conn, "disconnected")
            await safe_send(conn, "complete")
            device_conn_to_controller_conn[conn] = None
        elif parts[0] == "unavailable":
            in_conn = device_conn_to_controller_conn[conn]
            id_conn = [i[0] for i in id_to_device_conn.items() if i[1] == conn][0]
            if in_conn is not None:
                await safe_send(in_conn, "disconnected")
            await safe_send(conn, "complete")
            del device_conn_to_controller_conn[conn]
            del id_to_device_conn[id_conn]
        elif parts[0] == "control":
            device_id_conn = parts[1]
            device_conn = id_to_device_conn[device_id_conn]
            await safe_send(device_conn, message)
        print(device_conn_to_controller_conn)
        print(id_to_device_conn)


async def main():
    host, port = os.getenv("host"), os.getenv("port")
    async with serve(loop, host, port) as server:
        print(f"Started ws://{host}:{port}")
        await server.serve_forever()


asyncio.run(main())
