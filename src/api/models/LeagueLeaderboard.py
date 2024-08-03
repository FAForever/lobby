from api.models.ConfiguredModel import ConfiguredModel
from pydantic import Field


class LeagueLeaderboard(ConfiguredModel):
    technical_name: str = Field(alias="technicalName")
