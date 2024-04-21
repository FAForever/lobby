from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity
from api.models.ModVersion import ModVersion
from api.models.Player import Player
from api.models.ReviewsSummary import ReviewsSummary


@dataclass
class Mod(AbstractEntity):
    display_name: str
    recommended: bool
    author: str
    reviews_summary: ReviewsSummary | None
    uploader: Player | None
    version: ModVersion
