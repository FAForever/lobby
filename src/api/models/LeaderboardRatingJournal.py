from api.models.ConfiguredModel import ConfiguredModel
from api.models.GamePlayerStats import GamePlayerStats
from api.models.Leaderboard import Leaderboard
from pydantic import Field


class LeaderboardRatingJournal(ConfiguredModel):
    create_time:      str                    = Field(alias="createTime")
    update_time:      str                    = Field(alias="updateTime")
    deviation_after:  float                  = Field(alias="deviationAfter")
    deviation_before: float                  = Field(alias="deviationBefore")
    mean_after:       float                  = Field(alias="meanAfter")
    mean_before:      float                  = Field(alias="meanBefore")

    player_stats:     GamePlayerStats | None = Field(None, alias="gamePlayerStats")
    leaderboard:      Leaderboard | None     = Field(None)
