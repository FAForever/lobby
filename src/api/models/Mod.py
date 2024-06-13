from api.models.AbstractEntity import AbstractEntity
from api.models.ModVersion import ModVersion
from api.models.Player import Player
from api.models.ReviewsSummary import ReviewsSummary
from pydantic import Field


class Mod(AbstractEntity):
    display_name:    str                   = Field(alias="displayName")
    recommended:     bool
    author:          str
    reviews_summary: ReviewsSummary | None = Field(None, alias="reviewsSummary")
    uploader:        Player | None         = Field(None)
    version:         ModVersion            = Field(alias="latestVersion")
