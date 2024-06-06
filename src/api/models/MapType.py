from __future__ import annotations

from enum import Enum


class MapType(Enum):
    SKIRMISH = "skirmish"
    COOP = "campaign_coop"
    OTHER = ""

    @staticmethod
    def from_string(map_type: str) -> MapType:
        for mtype in list(MapType):
            if mtype.value == map_type:
                return mtype
        else:
            return MapType.OTHER
