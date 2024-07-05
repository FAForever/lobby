from api.models.ConfiguredModel import ConfiguredModel
from pydantic import Field


class NameRecord(ConfiguredModel):
    xd:          str = Field(alias="id")
    change_time: str = Field(alias="changeTime")
    name:        str
