from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueSeason import LeagueSeason
from pydantic import Field


class LeagueDivision(ConfiguredModel):
    xd:          str                 = Field(alias="id")
    description: str                 = Field(alias="descriptionKey")
    index:       int                 = Field(alias="divisionIndex")
    name:        str                 = Field(alias="nameKey")

    season:      LeagueSeason | None = Field(None, alias="leagueSeason")
