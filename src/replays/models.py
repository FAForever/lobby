from __future__ import annotations

from typing import Any
from typing import Callable

from PyQt6.QtCore import QObject
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon

import util
from api.models.Player import Player
from model.rating import Rating
from pydantic import BaseModel
from pydantic import Field
from qt.models.qtlistmodel import QtListModel


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


class ScoreboardModelItem(QObject):
    updated = pyqtSignal()

    def __init__(self, replay_data: dict, mod: str | None) -> None:
        QObject.__init__(self)
        self.replay_data = replay_data
        self.mod = mod or ""
        self.player = Player(**replay_data["player"])
        if len(self.replay_data["ratingChanges"]) > 0:
            self.rating_stats = self.replay_data["ratingChanges"][0]
        else:
            self.rating_stats = None

    @classmethod
    def builder(cls, mod: str | None) -> Callable[[dict], ScoreboardModelItem]:
        def build(data: dict) -> ScoreboardModelItem:
            return cls(data, mod)
        return build

    def score(self) -> int:
        return self.replay_data["score"]

    def login(self) -> str:
        return self.player.login

    def rating_before(self) -> int:
        # gamePlayerStats' fields 'before*' and 'after*' can be removed
        # at any time and 'ratingChanges' can be absent if game result is
        # undefined
        if self.rating_stats is not None:
            rating = Rating(
                self.rating_stats["meanBefore"],
                self.rating_stats["deviationBefore"],
            )
            return round(rating.displayed())
        elif self.replay_data.get("beforeMean") and self.replay_data.get("beforeDeviation"):
            rating = Rating(
                self.replay_data["beforeMean"],
                self.replay_data["beforeDeviation"],
            )
            return round(rating.displayed())
        return 0

    def rating_after(self) -> int:
        if self.rating_stats is not None:
            rating = Rating(
                self.rating_stats["meanAfter"],
                self.rating_stats["deviationAfter"],
            )
            return round(rating.displayed())
        elif self.replay_data.get("afterMean") and self.replay_data.get("afterDeviation"):
            rating = Rating(
                self.replay_data["afterMean"],
                self.replay_data["afterDeviation"],
            )
            return round(rating.displayed())
        return 0

    def rating(self) -> int | None:
        if self.rating_stats is None and "beforeMean" not in self.replay_data:
            return None
        return self.rating_before()

    def rating_change(self) -> int:
        if self.rating_stats is None:
            return 0
        return self.rating_after() - self.rating_before()

    def faction_name(self) -> str:
        if "faction" in self.replay_data:
            if self.replay_data["faction"] == 1:
                faction = "UEF"
            elif self.replay_data["faction"] == 2:
                faction = "Aeon"
            elif self.replay_data["faction"] == 3:
                faction = "Cybran"
            elif self.replay_data["faction"] == 4:
                faction = "Seraphim"
            elif self.replay_data["faction"] == 5:
                if self.mod == "nomads":
                    faction = "Nomads"
                else:
                    faction = "Random"
            elif self.replay_data["faction"] == 6:
                if self.mod == "nomads":
                    faction = "Random"
                else:
                    faction = "broken"
            else:
                faction = "broken"
        else:
            faction = "Missing"
        return faction

    def icon(self) -> QIcon:
        return util.THEME.icon(f"replays/{self.faction_name()}.png")


class ScoreboardModel(QtListModel):
    def __init__(
            self,
            spoiled: bool,
            alignment: Qt.AlignmentFlag,
            item_builder: Callable[[Any], QObject],
    ) -> None:
        QtListModel.__init__(self, item_builder)
        self.spoiled = spoiled
        self.alignment = alignment

    def get_alignment(self) -> Qt.AlignmentFlag:
        return self.alignment

    def add_player(self, player: dict) -> None:
        self._add_item(player, player["player"]["id"])
