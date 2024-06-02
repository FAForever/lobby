from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from api.models.CoopMission import CoopMission


class CoopScenario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    xd:          int = Field(alias="id")
    name:        str
    order:       int
    description: str | None
    faction:     str
    maps:        list[CoopMission]
