from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel
from src.api.models.LeagueSeason import LeagueSeason


class LeagueDivision(ConfiguredModel):
    xd:          str                 = Field(alias="id")
    description: str                 = Field(alias="descriptionKey")
    index:       int                 = Field(alias="divisionIndex")
    name:        str                 = Field(alias="nameKey")

    season:      LeagueSeason | None = Field(None, alias="leagueSeason")
