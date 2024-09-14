from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.ModVersion import ModVersion
from src.api.models.Player import Player
from src.api.models.ReviewsSummary import ReviewsSummary


class Mod(AbstractEntity):
    display_name:    str                   = Field(alias="displayName")
    recommended:     bool
    author:          str
    reviews_summary: ReviewsSummary | None = Field(None, alias="reviewsSummary")
    uploader:        Player | None         = Field(None)
    version:         ModVersion            = Field(alias="latestVersion")
