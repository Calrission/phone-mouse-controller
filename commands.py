import abc
import dataclasses
import inspect
from utils import flatten


class Command(abc.ABC):
    path: [str] = []
    command: str
    arguments: tuple[type, ...]

    is_support_path: bool

    def __init__(self, command: str, *arguments, is_support_path=True):
        self.is_support_path = is_support_path
        self.command = command
        self.arguments = arguments

    def command_with_path(self) -> str:
        result = self.command
        if len(self.path) != 0:
            result = "#".join(self.path) + "#" + result
        return result

    def parse(self, text: str) -> 'CommandInstance':
        parts = text.split("#")
        if not text.startswith(self.command_with_path()):
            raise ValueError(f"Command '{parts[0]}' does not match command '{self.command}'")
        args = parts[len(self.path)+1:]
        args_values = []
        for i, type_arg in enumerate(self.arguments):
            arg = args[i]
            if type_arg == int:
                arg = int(arg)
            elif type_arg == float:
                arg = float(arg)
            elif type_arg != str:
                raise ValueError(f'Not supported type "{type_arg}" on command "{self.command}"')
            args_values.append(arg)
        return CommandInstance(self, tuple(args_values))

    def instance(self, *args) -> 'CommandInstance':
        types_args = [type(i) for i in args]
        is_valid = all([e == self.arguments[i] for i, e in enumerate(types_args)])
        if not is_valid:
            raise TypeError(f"Need arguments: {self.arguments}, but given {types_args}")
        return CommandInstance(self, args)


@dataclasses.dataclass
class CommandInstance:
    command: Command
    arguments: tuple

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.arguments[item]
        raise TypeError(f"CommandInstance.__getitem__ using only int")

    def __str__(self):
        arguments = "#".join(map(str, self.arguments))
        result = self.command.command_with_path()
        if arguments != "":
            result += "#" + arguments
        return result


class MetaCommandsSet(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.path = [attrs["__str__"](cls)]

    def __getattribute__(cls, item):
        value_item = super().__getattribute__(item)
        if isinstance(value_item, Command):
            if value_item.is_support_path:
                value_item.path = cls.path
        elif isinstance(value_item, MetaCommandsSet):
            value_item.path = cls.path + value_item.path
        return value_item


class MouseCommands(metaclass=MetaCommandsSet):
    WHEEL = Command("wheel", int)
    LEFT = Command("left")
    RIGHT = Command("right")
    MIDDLE = Command("middle")

    def __str__(self):
        return "mouse"


class StatusCommands:
    STARTED = Command("started", is_support_path=False)
    CONNECTED = Command("connected", is_support_path=False)
    DISCONNECTED = Command("disconnected", is_support_path=False)


class AvailableCommands:
    AVAILABLE = Command("available", str, is_support_path=False)
    UNAVAILABLE = Command("unavailable", is_support_path=False)


class ControlCommands(metaclass=MetaCommandsSet):
    MOVE = Command("move", int, int)
    MOUSE = MouseCommands
    TAP = Command("tap", str)

    def __str__(self):
        return "control"


class COMMANDS:
    CONTROL = ControlCommands
    STATUS = StatusCommands
    AVAILABLE = AvailableCommands
    PING = Command("ping")

    @staticmethod
    def commands() -> [Command]:
        def from_dict(obj, d: dict):
            return [getattr(obj, i[0]) for i in d.items() if isinstance(i[1], Command)]

        return flatten([i if isinstance(i, Command) else from_dict(i, i.__dict__) for i in COMMANDS.__dict__.values() if
                        inspect.isclass(i)])

    @staticmethod
    def get_command(text: str) -> Command | None:
        commands = COMMANDS.commands()
        for command in commands:
            if text.startswith(command.command_with_path()):
                return command
        return None
