from pydantic import BaseModel
from pydantic import Field


# FIXME - this is what the widget uses so far, we should define this
# schema precisely in the future
class MetadataModel(BaseModel):
    complete: bool = Field(False)
    featured_mod: str | None
    launched_at: float
    mapname: str
    num_players: int
    teams: dict[str, list[str]]
    title: str
    game_time: float = Field(0.0)
