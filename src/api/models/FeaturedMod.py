from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel


class FeaturedMod(ConfiguredModel):
    xd:          str  = Field(alias="id")
    name:        str  = Field(alias="technicalName")
    fullname:    str  = Field(alias="displayName")
    visible:     bool
    order:       int  = Field(0)
    description: str  = Field("<i>No description provided</i>")
