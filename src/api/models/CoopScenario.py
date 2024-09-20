from pydantic import Field

from src.api.models.ConfiguredModel import ConfiguredModel
from src.api.models.CoopMission import CoopMission


class CoopScenario(ConfiguredModel):
    xd:          int = Field(alias="id")
    name:        str
    order:       int
    description: str | None
    faction:     str
    maps:        list[CoopMission]
