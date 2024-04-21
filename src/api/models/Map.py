from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity
from api.models.MapType import MapType
from api.models.MapVersion import MapVersion
from api.models.Player import Player
from api.models.ReviewsSummary import ReviewsSummary


@dataclass
class Map(AbstractEntity):
    display_name: str
    recommended: int
    author: Player | None
    reviews_summary: ReviewsSummary | None
    games_played: int
    maptype: MapType
    version: MapVersion | None = None
