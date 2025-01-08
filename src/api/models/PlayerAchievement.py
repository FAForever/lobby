from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.Achievement import Achievement
from src.api.models.Achievement import State
from src.api.models.Player import Player


class PlayerAchievement(AbstractEntity):
    current_steps: int | None         = Field(alias="currentSteps")
    state:         str

    achievement:   Achievement | None = Field(None)
    player:        Player | None      = Field(None)

    @property
    def current_state(self) -> State:
        return State(self.state)
