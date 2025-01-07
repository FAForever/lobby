from __future__ import annotations

from enum import Enum

from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtCore import Qt

from src.client.user import UserRelations
from src.games.filters.manager import GameFilterManager
from src.games.gamemodel import GameModel
from src.games.moditem import mod_invisible
from src.model.game import Game
from src.model.game import GameState


class GameSortModel(QSortFilterProxyModel):
    class SortType(Enum):
        PLAYER_NUMBER = 0
        AVERAGE_RATING = 1
        MAPNAME = 2
        HOSTNAME = 3
        AGE = 4

    def __init__(self, relations: UserRelations, model: GameModel) -> None:
        QSortFilterProxyModel.__init__(self)
        self._sort_type = self.SortType.AGE
        self.user_relations = relations
        self.setSourceModel(model)
        self.sort(0)

    def lessThan(self, leftIndex, rightIndex):
        left = self.sourceModel().data(leftIndex, Qt.ItemDataRole.DisplayRole).game
        right = self.sourceModel().data(rightIndex, Qt.ItemDataRole.DisplayRole).game

        comp_list = [self._lt_friend, self._lt_type, self._lt_fallback]

        for lt in comp_list:
            if lt(left, right):
                return True
            elif lt(right, left):
                return False
        return False

    def _lt_friend(self, left: Game, right: Game) -> bool:
        hostl = -1 if left.host_player is None else left.host_player.id
        hostr = -1 if right.host_player is None else right.host_player.id
        return (
            self.user_relations.model.is_friend(hostl)
            and not self.user_relations.model.is_friend(hostr)
        )

    def _lt_type(self, left, right):
        stype = self._sort_type
        stypes = self.SortType

        if stype == stypes.PLAYER_NUMBER:
            return len(left.players) > len(right.players)
        elif stype == stypes.AVERAGE_RATING:
            return left.average_rating > right.average_rating
        elif stype == stypes.MAPNAME:
            return left.mapdisplayname.lower() < right.mapdisplayname.lower()
        elif stype == stypes.HOSTNAME:
            return left.host.lower() < right.host.lower()
        elif stype == stypes.AGE:
            return left.uid < right.uid

    def _lt_fallback(self, left, right):
        return left.uid < right.uid

    @property
    def sort_type(self):
        return self._sort_type

    @sort_type.setter
    def sort_type(self, stype):
        self._sort_type = stype
        self.invalidate()

    def filterAcceptsRow(self, row, parent):
        index = self.sourceModel().index(row, 0, parent)
        if not index.isValid():
            return False
        game = index.data().game

        return self.filter_accepts_game(game)

    def filter_accepts_game(self, game):
        return True

    def total_games(self) -> int:
        return sum(
            game.state == GameState.OPEN and game.featured_mod != "coop"
            for game in self.sourceModel().games()
        )


class CustomGameFilterModel(GameSortModel):
    def __init__(self, relations: UserRelations, model: GameModel) -> None:
        GameSortModel.__init__(self, relations, model)
        self._hide_private_games = False
        self._hide_modded_games = False
        self.filter_manager = GameFilterManager()

    def filter_accepts_game(self, game: Game) -> bool:
        if game.state != GameState.OPEN:
            return False
        if game.featured_mod in mod_invisible or game.featured_mod == "coop":
            return False
        if self.hide_private_games and game.password_protected:
            return False
        if self.hide_modded_games and game.sim_mods:
            return False
        for game_filter in self.filter_manager.filters:
            if game_filter.rejects(game):
                return False

        return True

    @property
    def hide_private_games(self):
        return self._hide_private_games

    @hide_private_games.setter
    def hide_private_games(self, priv):
        self._hide_private_games = priv
        self.invalidateFilter()

    @property
    def hide_modded_games(self) -> bool:
        return self._hide_modded_games

    @hide_modded_games.setter
    def hide_modded_games(self, modded: bool) -> None:
        self._hide_modded_games = modded
        self.invalidateFilter()

    def manage_filters(self) -> None:
        self.filter_manager.exec()
        self.invalidateFilter()
