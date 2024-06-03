from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel
from api.models.Player import Player


class PlayerStats(ConfiguredModel):
    player: Player | None = Field(None)
