from pydantic import Field
from pydantic import field_validator

from src.api.models.ConfiguredModel import ConfiguredModel


class ReviewsSummary(ConfiguredModel):
    positive:      float
    negative:      float
    score:         float
    average_score: float = Field(alias="averageScore")
    num_reviews:   int   = Field(alias="reviews")
    lower_bound:   float = Field(alias="lowerBound")

    @field_validator("*", mode="before")
    @classmethod
    def avoid_none(cls, value: float | int | None) -> float | int:
        return value or 0
