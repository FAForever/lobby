from collections.abc import ValuesView

from src.client.user import User
from src.client.user import UserRelations
from src.downloadManager import MapPreviewDownloader
from src.model.game import Game
from src.model.gameset import Gameset
from src.qt.models.qtlistmodel import QtListModel

from .gamemodelitem import GameModelItem


class GameModel(QtListModel):
    def __init__(
            self,
            relations: UserRelations,
            me: User,
            preview_dler: MapPreviewDownloader,
            gameset: Gameset | None = None,
    ) -> None:
        builder = GameModelItem.builder(relations, me, preview_dler)
        QtListModel.__init__(self, builder)

        self._gameset = gameset
        if self._gameset is not None:
            self._gameset.added.connect(self.add_game)
            self._gameset.newClosedGame.connect(self.remove_game)
            for game in self._gameset.values():
                self.add_game(game)

    def add_game(self, game):
        self._add_item(game, game.uid)

    def remove_game(self, game):
        self._remove_item(game.uid)

    def clear_games(self):
        self._clear_items()

    def games(self) -> ValuesView[Game]:
        assert self._gameset is not None
        return self._gameset.values()
