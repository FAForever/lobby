from api.models.AbstractEntity import AbstractEntity
from api.models.Leaderboard import Leaderboard
from api.models.Player import Player
from pydantic import Field


class LeaderboardRating(AbstractEntity):
    deviation:   float
    mean:        float
    total_games: int                = Field(alias="totalGames")
    rating:      float
    won_games:   int                = Field(alias="wonGames")

    leaderboard: Leaderboard | None = Field(None)
    player:      Player | None      = Field(None)
