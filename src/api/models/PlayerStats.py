from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel
from src.api.models.Player import Player


class PlayerStats(ConfiguredModel):
    player: Player | None = Field(None)
