from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel


class NameRecord(ConfiguredModel):
    xd:          str = Field(alias="id")
    change_time: str = Field(alias="changeTime")
    name:        str
