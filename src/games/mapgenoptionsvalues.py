from enum import Enum
from operator import attrgetter
from typing import Any


class ValuesListableEnum(Enum):

    @classmethod
    def values(cls) -> list[Any]:
        return list(map(attrgetter("value"), iter(cls)))


class Sentinel(ValuesListableEnum):
    RANDOM = "RANDOM"


class GenerationType(ValuesListableEnum):
    CASUAL = "CASUAL"
    TOURNAMENT = "TOURNAMENT"
    BLIND = "BLIND"
    UNEXPLORED = "UNEXPLORED"


class TerrainSymmetry(ValuesListableEnum):
    POINT2 = "POINT2"
    POINT3 = "POINT3"
    POINT4 = "POINT4"
    POINT5 = "POINT5"
    POINT6 = "POINT6"
    POINT7 = "POINT7"
    POINT8 = "POINT8"
    POINT9 = "POINT9"
    POINT10 = "POINT10"
    POINT11 = "POINT11"
    POINT12 = "POINT12"
    POINT13 = "POINT13"
    POINT14 = "POINT14"
    POINT15 = "POINT15"
    POINT16 = "POINT16"
    XZ = "XZ"
    ZX = "ZX"
    X = "X"
    Z = "Z"
    QUAD = "QUAD"
    DIAG = "DIAG"
    NONE = "NONE"


class MapStyle(ValuesListableEnum):
    BASIC = "BASIC"
    BIG_ISLANDS = "BIG_ISLANDS"
    CENTER_LAKE = "CENTER_LAKE"
    DROP_PLATEAU = "DROP_PLATEAU"
    FLOODED = "FLOODED"
    HIGH_RECLAIM = "HIGH_RECLAIM"
    LAND_BRIDGE = "LAND_BRIDGE"
    LITTLE_MOUNTAIN = "LITTLE_MOUNTAIN"
    LOW_MEX = "LOW_MEX"
    MOUNTAIN_RANGE = "MOUNTAIN_RANGE"
    ONE_ISLAND = "ONE_ISLAND"
    SMALL_ISLANDS = "SMALL_ISLANDS"
    VALLEY = "VALLEY"


class TerrainStyle(ValuesListableEnum):
    BASIC = "BASIC"
    BIG_ISLANDS = "BIG_ISLANDS"
    CENTER_LAKE = "CENTER_LAKE"
    DROP_PLATEAU = "DROP_PLATEAU"
    FLOODED = "FLOODED"
    LAND_BRIDGE = "LAND_BRIDGE"
    LITTLE_MOUNTAIN = "LITTLE_MOUNTAIN"
    MOUNTAIN_RANGE = "MOUNTAIN_RANGE"
    ONE_ISLAND = "ONE_ISLAND"
    SMALL_ISLANDS = "SMALL_ISLANDS"
    VALLEY = "VALLEY"


class PropStyle(ValuesListableEnum):
    BASIC = "BASIC"
    BOULDER_FIELD = "BOULDER_FIELD"
    ENEMY_CIV = "ENEMY_CIV"
    HIGH_RECLAIM = "HIGH_RECLAIM"
    LARGE_BATTLE = "LARGE_BATTLE"
    NAVY_WRECKS = "NAVY_WRECKS"
    NEUTRAL_CIV = "NEUTRAL_CIV"
    ROCK_FIELD = "ROCK_FIELD"
    SMALL_BATTLE = "SMALL_BATTLE"


class ResourceStyle(ValuesListableEnum):
    BASIC = "BASIC"
    LOW_MEX = "LOW_MEX"
    WATER_MEX = "WATER_MEX"


class TextureStyle(ValuesListableEnum):
    BRIMSTONE = "BRIMSTONE"
    DESERT = "DESERT"
    EARLYAUTUMN = "EARLYAUTUMN"
    FRITHEN = "FRITHEN"
    MARS = "MARS"
    MOONLIGHT = "MOONLIGHT"
    PRAYER = "PRAYER"
    STONES = "STONES"
    SUNSET = "SUNSET"
    SYRTIS = "SYRTIS"
    WINDINGRIVER = "WINDINGRIVER"
    WONDER = "WONDER"
