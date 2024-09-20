from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel


class LeagueLeaderboard(ConfiguredModel):
    technical_name: str = Field(alias="technicalName")
