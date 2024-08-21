import struct
from enum import Enum
from io import BufferedReader
from typing import Any


class LuaDataType(Enum):
    NUMBER = 0
    STRING = 1
    NIL = 2
    BOOL = 3
    TABLE_START = 4
    TABLE_END = 5


class ReplayParser:
    def __init__(self, file: str) -> None:
        self.file = file

    def parse_header(self) -> dict[str, Any]:
        with open(self.file, "rb") as stream:
            data_parser = ReplayDataParser(stream)
            return data_parser.parse_header()


class ReplayDataParser:
    def __init__(self, stream: BufferedReader) -> None:
        self.stream = stream
        self.buffer = b""

    def unpack(self, fmt: str, packed: bytes) -> Any:
        value, *_ = struct.unpack(fmt, packed)
        return value

    def advance(self, fmt: str) -> None:
        size = struct.calcsize(fmt)
        self.buffer = self.buffer[size:]

    def peek(self, fmt: str) -> Any:
        size = struct.calcsize(fmt)
        incoming = self.stream.read(size)
        self.buffer += incoming
        return self.unpack(fmt, incoming)

    def read(self, fmt: str) -> Any:
        if self.buffer:
            value = self.unpack(fmt, self.buffer)
        else:
            value = self.peek(fmt)
        self.advance(fmt)
        return value

    def read_string(self) -> str:
        line = b""
        while self.peek("c") != b"\x00":
            line += self.read("s")
        self.advance("c")
        try:
            return line.decode()
        except UnicodeDecodeError:
            return ""

    def read_int(self) -> int:
        return self.read("<i")

    def read_float(self) -> float:
        return self.read("<f")

    def read_unsigned_char(self) -> int:
        return self.read("B")

    def parse_lua(self) -> Any:
        data_type = LuaDataType(self.read_unsigned_char())
        match data_type:
            case LuaDataType.NUMBER:
                return self.read_float()
            case LuaDataType.NIL:
                self.advance("B")
                return None
            case LuaDataType.BOOL:
                return bool(self.read_unsigned_char())
            case LuaDataType.STRING:
                return self.read_string()
            case LuaDataType.TABLE_START:
                lua_table = {}
                while LuaDataType(self.peek("B")) != LuaDataType.TABLE_END:
                    key = self.parse_lua()
                    value = self.parse_lua()
                    lua_table[key] = value
                self.advance("B")
                return lua_table
            case _:
                raise ValueError(f"Unknown data type: {data_type=}")

    def _game_version(self, supcom_version: str) -> int | None:
        if supcom_version.startswith("Supreme Commander v1"):
            return int(supcom_version.split(".")[-1])
        return None

    def _mapname(self, map_path: str) -> str | None:
        return map_path.split("/")[2] if map_path.startswith("/maps/") else None

    def parse_header(self) -> dict[str, Any]:
        header = {}
        header["game_version"] = self._game_version(self.read_string())

        self.read_string()  # newline

        replay_version, map_path = self.read_string().split("\r\n")
        header["replay_version"] = replay_version
        header["mapname"] = self._mapname(map_path)

        self.read_string()  # garbage
        self.read_int()  # length of sim_mods table in bytes

        header["sim_mods"] = self.parse_lua()
        return header
