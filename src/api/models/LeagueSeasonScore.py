from api.models.ConfiguredModel import ConfiguredModel
from api.models.LeagueSeason import LeagueSeason
from api.models.LeagueSubdivision import LeagueSubdivision
from pydantic import Field


class LeagueSeasonScore(ConfiguredModel):
    game_count:       int                      = Field(alias="gameCount")
    login_id:         int                      = Field(alias="loginId")
    returning_player: bool                     = Field(alias="returningPlayer")
    score:            int | None

    subdivision:      LeagueSubdivision | None = Field(None, alias="leagueSeasonDivisionSubdivision")
    season:           LeagueSeason | None      = Field(None, alias="leagueSeason")
