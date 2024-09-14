from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel


class GamePlayerStats(ConfiguredModel):
    xd:         str  = Field(alias="id")
    ai:         bool
    color:      int
    faction:    int
    result:     str
    score:      int
    score_time: str  = Field(alias="scoreTime")
    start_spot: int  = Field(alias="startSpot")
    team:       int
