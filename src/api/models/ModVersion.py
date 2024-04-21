from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity
from api.models.ModType import ModType


@dataclass
class ModVersion(AbstractEntity):
    description: str
    download_url: str
    filename: str
    hidden: bool
    ranked: bool
    thumbnail_url: str
    modtype: ModType
    version: str
