from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.MapType import MapType
from src.api.models.MapVersion import MapVersion
from src.api.models.Player import Player
from src.api.models.ReviewsSummary import ReviewsSummary


class Map(AbstractEntity):
    display_name:    str                   = Field(alias="displayName")
    recommended:     int
    author:          Player | None         = Field(None)
    reviews_summary: ReviewsSummary | None = Field(None, alias="reviewsSummary")
    games_played:    int                   = Field(alias="gamesPlayed")
    map_type:        str                   = Field(alias="mapType")
    version:         MapVersion | None     = Field(None)

    @property
    def maptype(self) -> MapType:
        return MapType.from_string(self.map_type)
