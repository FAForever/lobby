from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel
from src.api.models.LeagueSeason import LeagueSeason
from src.api.models.LeagueSubdivision import LeagueSubdivision


class LeagueSeasonScore(ConfiguredModel):
    game_count:       int                      = Field(alias="gameCount")
    login_id:         int                      = Field(alias="loginId")
    returning_player: bool                     = Field(alias="returningPlayer")
    score:            int | None

    subdivision:      LeagueSubdivision | None = Field(None, alias="leagueSeasonDivisionSubdivision")
    season:           LeagueSeason | None      = Field(None, alias="leagueSeason")
