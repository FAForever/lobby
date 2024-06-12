from api.models.AbstractEntity import AbstractEntity
from pydantic import Field


class Leaderboard(AbstractEntity):
    description:     str = Field(alias="descriptionKey")
    name:            str = Field(alias="nameKey")
    technical_name:  str = Field(alias="technicalName")
