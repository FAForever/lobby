from pydantic import BaseModel
from pydantic import Field

from api.models.CoopMission import CoopMission


class CoopScenario(BaseModel):
    uid: int = Field(alias="id")
    name: str
    order: int
    description: str | None
    faction: str
    maps: list[CoopMission]
