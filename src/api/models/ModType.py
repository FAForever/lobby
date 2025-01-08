from __future__ import annotations

from enum import Enum


class ModType(Enum):
    UI = "UI"
    SIM = "SIM"
    OTHER = ""

    @staticmethod
    def from_string(string: str) -> ModType:
        if string in ModType:
            return ModType(string)
        return ModType.OTHER
