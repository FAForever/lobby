from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueSeason import LeagueSeason
from pydantic import Field
from pydantic import field_validator


class LeagueDivision(ConfiguredModel):
    xd:          str                 = Field(alias="id")
    description: str                 = Field(alias="descriptionKey")
    index:       int                 = Field(alias="divisionIndex")
    name:        str                 = Field(alias="nameKey")

    season:      LeagueSeason | None = Field(None, alias="leagueSeason")

    @classmethod
    @field_validator("season", mode="before")
    def validate_season(cls, value: dict) -> LeagueSeason | None:
        if not value:
            return None
        return LeagueSeason(**value)
