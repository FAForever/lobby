from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel
from src.api.models.Game import Game


class CoopResult(ConfiguredModel):
    xd:                   str         = Field(alias="id")
    duration:             int
    mission:              int
    player_count:         int         = Field(alias="playerCount")
    secondary_objectives: bool        = Field(alias="secondaryObjectives")

    game:                 Game | None = Field(None)
