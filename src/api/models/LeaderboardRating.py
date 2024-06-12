from api.models.AbstractEntity import AbstractEntity
from api.models.Leaderboard import Leaderboard
from api.models.Player import Player
from pydantic import Field
from pydantic import field_validator


class LeaderboardRating(AbstractEntity):
    deviation:   float
    mean:        float
    total_games: int                = Field(alias="totalGames")
    rating:      float
    won_games:   int                = Field(alias="wonGames")

    leaderboard: Leaderboard | None = Field(None)
    player:      Player | None      = Field(None)

    @classmethod
    @field_validator("leaderboard", mode="before")
    def validate_leaderboard(cls, value: dict) -> Leaderboard | None:
        if not value:
            return None
        return Leaderboard(**value)

    @classmethod
    @field_validator("player", mode="before")
    def validate_player(cls, value: dict) -> Player | None:
        if not value:
            return None
        return Player(**value)
