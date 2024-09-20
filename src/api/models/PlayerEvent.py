from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.Event import Event
from src.api.models.Player import Player


class PlayerEvent(AbstractEntity):
    current_count: int           = Field(alias="currentCount")

    event:         Event | None  = Field(None)
    player:        Player | None = Field(None)
