from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueDivision import LeagueDivision
from pydantic import Field


class LeagueSubdivision(ConfiguredModel):
    index:            int                   = Field(alias="subdivisionIndex")
    name:             str                   = Field(alias="nameKey")
    description:      str                   = Field(alias="descriptionKey")
    highest_score:    int                   = Field(alias="highestScore")
    max_rating:       int                   = Field(alias="maxRating")
    min_rating:       int                   = Field(alias="minRating")
    image_url:        str                   = Field(alias="imageUrl")
    small_image_url:  str                   = Field(alias="smallImageUrl")
    medium_image_url: str                   = Field(alias="mediumImageUrl")

    division:         LeagueDivision | None = Field(None, alias="leagueSeasonDivision")
