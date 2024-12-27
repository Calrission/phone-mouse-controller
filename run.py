import uuid

import keyboard
import mouse
from mouse import MIDDLE

from commands import COMMANDS, AvailableCommands
from qr import generate_qr_code
from ws_client import WsClient

ws_client = WsClient("localhost", 5121)


@ws_client.on(COMMANDS.CONTROL.MOVE)
async def move(dx: int, dy: int):
    x, y = mouse.get_position()
    mouse.move(x + dx, y + dy)


@ws_client.on(COMMANDS.CONTROL.MOUSE.RIGHT)
async def mouse_right_click():
    mouse.right_click()


@ws_client.on(COMMANDS.CONTROL.MOUSE.LEFT)
async def mouse_left_click():
    mouse.click()


@ws_client.on(COMMANDS.CONTROL.MOUSE.WHEEL)
async def mouse_wheel(delta: int):
    mouse.wheel(delta)


@ws_client.on(COMMANDS.CONTROL.MOUSE.MIDDLE)
async def mouse_middle_click():
    mouse.click(MIDDLE)


@ws_client.on(COMMANDS.CONTROL.TAP)
async def tap(btn: str):
    keyboard.press_and_release(btn)


@ws_client.on(COMMANDS.STATUS.CONNECTED)
async def connected():
    print("Connected")


@ws_client.on(COMMANDS.STATUS.DISCONNECTED)
async def disconnected():
    print("Disconnected")


@ws_client.on(COMMANDS.PING)
async def ping():
    await ws_client.send("pong")


@ws_client.on(COMMANDS.STATUS.STARTED)
async def started():
    print("Started")
    ID = str(uuid.uuid4())
    qr_terminal = generate_qr_code(ID)
    print(qr_terminal)
    await ws_client.send(AvailableCommands.AVAILABLE.instance(ID))

ws_client.start()
