from pydantic import BaseModel
from pydantic import Field

from api.models.Player import Player
from api.models.PlayerStats import PlayerStats


class Game(BaseModel):
    end_time:         str                      = Field(alias="endTime")
    xd:               str                      = Field(alias="id")
    name:             str
    replay_available: bool                     = Field(alias="replayAvailable")
    replay_ticks:     int | None               = Field(alias="replayTicks")
    replay_url:       str                      = Field(alias="replayUrl")
    start_time:       str                      = Field(alias="startTime")

    host:             Player | None            = Field(None)
    player_stats:     list[PlayerStats] | None = Field(None, alias="playerStats")
