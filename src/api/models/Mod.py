from pydantic import Field
from pydantic import field_validator

from api.models.AbstractEntity import AbstractEntity
from api.models.ModVersion import ModVersion
from api.models.Player import Player
from api.models.ReviewsSummary import ReviewsSummary


class Mod(AbstractEntity):
    display_name:    str                   = Field(alias="displayName")
    recommended:     bool
    author:          str
    reviews_summary: ReviewsSummary | None = Field(None, alias="reviewsSummary")
    uploader:        Player | None         = Field(None)
    version:         ModVersion            = Field(alias="latestVersion")

    @field_validator("reviews_summary", mode="before")
    @classmethod
    def validate_reviews_summary(cls, value: dict) -> ReviewsSummary | None:
        if not value:
            return None
        return ReviewsSummary(**value)

    @field_validator("uploader", mode="before")
    @classmethod
    def validate_uploader(cls, value: dict) -> Player | None:
        if not value:
            return None
        return Player(**value)
