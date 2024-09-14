from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel


class Event(ConfiguredModel):
    xd:        str        = Field(alias="id")
    name:      str
    image_url: str | None = Field(alias="imageUrl")
    typ:       str        = Field(alias="type")
