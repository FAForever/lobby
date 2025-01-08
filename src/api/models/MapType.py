from __future__ import annotations

from enum import Enum


class MapType(Enum):
    SKIRMISH = "skirmish"
    COOP = "campaign_coop"
    OTHER = ""

    @staticmethod
    def from_string(map_type: str) -> MapType:
        if map_type in MapType:
            return MapType(map_type)
        return MapType.OTHER
