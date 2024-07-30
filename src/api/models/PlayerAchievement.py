from api.models.AbstractEntity import AbstractEntity
from api.models.Achievement import Achievement
from api.models.Achievement import State
from api.models.Player import Player
from pydantic import Field


class PlayerAchievement(AbstractEntity):
    current_steps: int | None         = Field(alias="currentSteps")
    state:         str

    achievement:   Achievement | None = Field(None)
    player:        Player | None      = Field(None)

    @property
    def current_state(self) -> State:
        return State.from_string(self.state)
