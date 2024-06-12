from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueSeason import LeagueSeason
from api.models.LeagueSubdivision import LeagueSubdivision
from pydantic import Field
from pydantic import field_validator


class LeagueSeasonScore(ConfiguredModel):
    game_count:       int                      = Field(alias="gameCount")
    login_id:         int                      = Field(alias="loginId")
    returning_player: bool                     = Field(alias="returningPlayer")
    score:            int | None

    subdivision:      LeagueSubdivision | None = Field(None, alias="leagueSeasonDivisionSubdivision")
    season:           LeagueSeason | None      = Field(None, alias="leagueSeason")

    @field_validator("subdivision", mode="before")
    @classmethod
    def validate_subdivision(cls, value: dict) -> LeagueSubdivision | None:
        if not value:
            return None
        return LeagueSubdivision(**value)

    @field_validator("season", mode="before")
    @classmethod
    def validate_season(cls, value: dict) -> LeagueSeason | None:
        if not value:
            return None
        return LeagueSeason(**value)
