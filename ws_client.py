import asyncio
from typing import Coroutine

from websockets import connect, ConnectionClosed

from commands import Command, COMMANDS, StatusCommands, CommandInstance


class WsClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.connection = None

        self.callbacks: dict[Command, [Coroutine]] = {}

    @property
    def url(self):
        return "ws://" + self.host + ":" + str(self.port)

    async def do_connect(self):
        async with connect(self.url) as connection:
            self.connection = connection
            await self.loop()

    def start(self):
        asyncio.run(self.do_connect())

    async def loop(self):
        await self.call_callback(StatusCommands.STARTED.instance())
        try:
            while True:
                message = await self.connection.recv()
                command = COMMANDS.get_command(message)
                if command is not None:
                    try:
                        command_instance = command.parse(message)
                        await self.call_callback(command_instance)
                    except ValueError as e:
                        print(e)
        except ConnectionClosed as e:
            print("Closed")
        except Exception as e:
            print(e)

    async def send(self, message: CommandInstance | str):
        print(f"SEND - {message}")
        await self.connection.send(str(message))

    def add_callback(self, command: Command, callback: Coroutine):
        if command not in self.callbacks:
            self.callbacks[command] = [callback]
        else:
            self.callbacks[command].append(callback)

    async def call_callback(self, command_instance: CommandInstance):
        for callback in self.callbacks[command_instance.command]:
            await callback(*command_instance.arguments)

    def remove_callback(self, command: Command, callback: Coroutine):
        if command in self.callbacks and callback in self.callbacks[command]:
            self.callbacks[command].remove(callback)

    def on(self, command: Command):
        def decorator(func):
            self.add_callback(command, func)
            return func

        return decorator
