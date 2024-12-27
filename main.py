import asyncio
import uuid
import mouse
from websockets.asyncio.client import connect

ID = str(uuid.uuid4())

is_connected = False

print(ID)


async def loop():
    global is_connected
    uri = "ws://localhost:5121"
    async with connect(uri) as ws:
        await ws.send(f"available#{ID}")
        async for message in ws:
            if message == "connected":
                is_connected = True
            elif message == "disconnected":
                is_connected = False
            elif message.startswith("control"):
                _, __, dx, dy = message.split("#")
                x, y = mouse.get_position()
                mouse.move(x+int(dx), y+int(dy))


if __name__ == "__main__":
    asyncio.run(loop())
