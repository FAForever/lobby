from __future__ import annotations

from enum import Enum

from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity


class State(Enum):
    REVEALED = "REVEALED"
    UNLOCKED = "UNLOCKED"


class ProgressType(Enum):
    STANDARD = "STANDARD"
    INCREMENTAL = "INCREMENTAL"


class Achievement(AbstractEntity):
    description:            str
    experience_points:      int        = Field(alias="experiencePoints")
    initial_state:          str        = Field(alias="initialState")
    name:                   str
    order:                  int
    revealed_icon_url:      str        = Field(alias="revealedIconUrl")
    total_steps:            int | None = Field(alias="totalSteps")
    typ:                    str        = Field(alias="type")
    unlocked_icon_url:      str        = Field(alias="unlockedIconUrl")
    unlockers_avg_duration: int | None = Field(alias="unlockersAvgDuration")
    unlockers_count:        int | None = Field(alias="unlockersCount")
    unlockers_max_duration: int | None = Field(alias="unlockersMaxDuration")
    unlockers_min_duration: int | None = Field(alias="unlockersMinDuration")
    unlockers_percent:      float      = Field(alias="unlockersPercent")

    @property
    def init_state(self) -> State:
        return State(self.initial_state)

    @property
    def progress_type(self) -> ProgressType:
        return ProgressType(self.typ)
