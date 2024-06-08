from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel
from api.models.CoopMission import CoopMission


class CoopScenario(ConfiguredModel):
    xd:          int = Field(alias="id")
    name:        str
    order:       int
    description: str | None
    faction:     str
    maps:        list[CoopMission]
