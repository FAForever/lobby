from api.models.AbstractEntity import AbstractEntity
from api.models.Event import Event
from api.models.Player import Player
from pydantic import Field


class PlayerEvent(AbstractEntity):
    current_count: int           = Field(alias="currentCount")

    event:         Event | None  = Field(None)
    player:        Player | None = Field(None)
