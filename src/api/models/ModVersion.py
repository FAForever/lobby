from pydantic import Field

from api.models.AbstractEntity import AbstractEntity
from api.models.ModType import ModType


class ModVersion(AbstractEntity):
    description:   str
    download_url:  str  = Field(alias="downloadUrl")
    filename:      str
    hidden:        bool
    ranked:        bool
    thumbnail_url: str  = Field(alias="thumbnailUrl")
    typ:           str  = Field(alias="type")
    version:       int
    uid:           str

    @property
    def modtype(self) -> ModType:
        return ModType.from_string(self.typ)
