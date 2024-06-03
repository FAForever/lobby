from pydantic import BaseModel
from pydantic import Field


class FeaturedMod(BaseModel):
    xd:          str  = Field(alias="id")
    name:        str  = Field(alias="technicalName")
    fullname:    str  = Field(alias="displayName")
    visible:     bool
    order:       int  = Field(0)
    description: str  = Field("<i>No description provided</i>")
