from api.models.ConfiguredModel import ConfiguredModel
from pydantic import Field


class Event(ConfiguredModel):
    xd:        str        = Field(alias="id")
    name:      str
    image_url: str | None = Field(alias="imageUrl")
    typ:       str        = Field(alias="type")
