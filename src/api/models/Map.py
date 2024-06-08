from pydantic import Field
from pydantic import field_validator

from api.models.AbstractEntity import AbstractEntity
from api.models.MapType import MapType
from api.models.MapVersion import MapVersion
from api.models.Player import Player
from api.models.ReviewsSummary import ReviewsSummary


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

    @field_validator("reviews_summary", mode="before")
    @classmethod
    def validate_reviews_summary(cls, value: dict) -> ReviewsSummary | None:
        if not value:
            return None
        return ReviewsSummary(**value)

    @field_validator("author", mode="before")
    @classmethod
    def validate_author(cls, value: dict) -> Player | None:
        if not value:
            return None
        return Player(**value)
