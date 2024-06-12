from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueLeaderboard import LeagueLeaderboard
from pydantic import Field
from pydantic import field_validator


class LeagueSeason(ConfiguredModel):
    end_date:           str                = Field(alias="endDate")
    name:               str                = Field(alias="nameKey")
    placement_games:    int                = Field(alias="placementGames")
    placement_games_rp: int                = Field(alias="placementGamesReturningPlayer")
    season_number:      int                = Field(alias="seasonNumber")
    start_date:         str                = Field(alias="startDate")

    leaderboard:        LeagueLeaderboard | None = Field(None)

    @classmethod
    @field_validator("leaderboard", mode="before")
    def validate_LeagueLeaderboard(cls, value: dict) -> LeagueLeaderboard | None:
        if not value:
            return None
        return LeagueLeaderboard(**value)
