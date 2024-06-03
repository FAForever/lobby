from __future__ import annotations

from enum import Enum


class ModType(Enum):
    UI = "UI"
    SIM = "SIM"
    OTHER = ""

    @staticmethod
    def from_string(string: str) -> ModType:
        for modtype in list(ModType):
            if modtype.value == string:
                return modtype
        return ModType.OTHER
