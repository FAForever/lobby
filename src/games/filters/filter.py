from __future__ import annotations

import operator
from typing import NamedTuple

from src.model.game import Game

FILTER_OPTIONS = {
    "Map name": str,
    "Host name": str,
    "Game title": str,
    "Average rating": int,
    "Featured mod": str,
}

FILTER_OPERATIONS = {
    "contains": operator.contains,
    "starts with": str.startswith,
    "ends with": str.endswith,
    "equals": operator.eq,
    "not equals": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


class GameFilter(NamedTuple):
    uid: int
    name: str
    constraint: str
    value: str

    def serialize(self) -> str:
        return f"{self.name},{self.constraint},{self.value}"

    def rejects(self, game: Game) -> bool:
        op = FILTER_OPERATIONS[self.constraint]
        if self.name == "Map name":
            return op(game.mapdisplayname.casefold(), self.value.casefold())
        elif self.name == "Host name":
            return op(game.host.casefold(), self.value.casefold())
        elif self.name == "Game title":
            return op(game.title.casefold(), self.value.casefold())
        elif self.name == "Featured mod":
            return op(game.featured_mod.casefold(), self.value.casefold())
        elif self.name == "Average rating":
            try:
                return op(game.average_rating, int(self.value))
            except (TypeError, ValueError):
                pass
        return True

    def accepts(self, game: Game) -> bool:
        return not self.rejects(game)
