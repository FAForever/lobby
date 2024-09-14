from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.Leaderboard import Leaderboard


class LeaderboardRating(AbstractEntity):
    deviation:   float
    mean:        float
    total_games: int                = Field(alias="totalGames")
    rating:      float
    won_games:   int                = Field(alias="wonGames")

    leaderboard: Leaderboard | None = Field(None)
