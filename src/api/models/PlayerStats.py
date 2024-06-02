from pydantic import BaseModel
from pydantic import Field

from api.models.Player import Player


class PlayerStats(BaseModel):
    player: Player | None = Field(None)
