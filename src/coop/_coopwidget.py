from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtNetwork import QNetworkRequest

import fa
import util
from api.coop_api import CoopApiAccessor
from api.coop_api import CoopResultApiAccessor
from api.models.CoopResult import CoopResult
from api.models.CoopScenario import CoopScenario
from client.user import User
from coop.coopmapitem import CoopMapItem
from coop.coopmapitem import CoopMapItemDelegate
from coop.coopmodel import CoopGameFilterModel
from coop.cooptableitemdelegate import CoopLeaderboardItemDelegate
from coop.cooptablemodel import CoopLeaderBoardModel
from fa.replay import replay
from games.gameitem import GameViewBuilder
from games.gamemodel import GameModel
from games.hostgamewidget import GameLauncher
from model.game import Game
from qt.utils import qopen
from ui.busy_widget import BusyWidget

if TYPE_CHECKING:
    from client._clientwindow import ClientWindow

logger = logging.getLogger(__name__)

FormClass, BaseClass = util.THEME.loadUiType("coop/coop.ui")


class CoopWidget(FormClass, BaseClass, BusyWidget):
    def __init__(
            self,
            client: ClientWindow,
            game_model: GameModel,
            me: User,
            gameview_builder: GameViewBuilder,
            game_launcher: GameLauncher,
    ) -> None:

        BaseClass.__init__(self)

        self.setupUi(self)

        self.client = client  # type - ClientWindow
        self._me = me
        self._game_model = CoopGameFilterModel(self._me, game_model)
        self._game_launcher = game_launcher
        self._gameview_builder = gameview_builder

        # Ranked search UI
        self.ispassworded = False
        self.loaded = False

        self.coop = {}
        self.cooptypes = {}

        self.options = []

        self.coop_api = CoopApiAccessor()
        self.coop_api.data_ready.connect(self.process_coop_info)

        self.coop_result_api = CoopResultApiAccessor()
        self.coop_result_api.data_ready.connect(self.process_leaderboard_infos)

        self.coopList.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
        )
        self.coopList.setItemDelegate(CoopMapItemDelegate(self))

        self.gameview = self._gameview_builder(self._game_model, self.gameList)
        self.gameview.game_double_clicked.connect(self.game_double_clicked)

        self.coopList.itemDoubleClicked.connect(self.coop_list_double_clicked)
        self.coopList.itemClicked.connect(self.coop_list_clicked)

        self.client.lobby_info.coopLeaderBoard.connect(self.process_leaderboard_infos)
        self.tabLeaderWidget.currentChanged.connect(self.ask_leaderboard)

        self.leaderBoard.setVisible(0)

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        self.leaderBoardTextGeneral.url_clicked.connect(self.open_url)
        self.leaderBoardTextOne.url_clicked.connect(self.open_url)
        self.leaderBoardTextTwo.url_clicked.connect(self.open_url)
        self.leaderBoardTextThree.url_clicked.connect(self.open_url)
        self.leaderBoardTextFour.url_clicked.connect(self.open_url)

        self.replay_download = QNetworkAccessManager()
        self.replay_download.finished.connect(self.finish_request)

        self.selectedItem = None

    def load_stylesheet(self):
        self.setStyleSheet(
            util.THEME.readstylesheet("coop/formatters/style.css"),
        )

    def _addExistingGames(self, gameset):
        for game in gameset.values():
            self._addGame(game)

    @QtCore.pyqtSlot(QtCore.QUrl)
    def open_url(self, url: QtCore.QUrl) -> None:
        self.replay_download.get(QNetworkRequest(url))

    def finish_request(self, reply: QNetworkReply) -> None:
        filepath = os.path.join(util.CACHE_DIR, "temp.fafreplay")
        open_mode = QtCore.QIODevice.OpenModeFlag.WriteOnly | QtCore.QIODevice.OpenModeFlag.Truncate
        with qopen(filepath, open_mode) as faf_replay:
            faf_replay.write(reply.readAll())
        replay(os.path.join(util.CACHE_DIR, "temp.fafreplay"))

    def process_leaderboard_infos(self, message: dict[str, list[CoopResult]]):
        """ Process leaderboard"""

        self.tabLeaderWidget.setEnabled(True)
        table = self.tabLeaderWidget.currentIndex()
        if table == 0:
            w = self.leaderBoardTextGeneral
        elif table == 1:
            w = self.leaderBoardTextOne
        elif table == 2:
            w = self.leaderBoardTextTwo
        elif table == 3:
            w = self.leaderBoardTextThree
        elif table == 4:
            w = self.leaderBoardTextFour
        model = CoopLeaderBoardModel(message)
        w.setModel(model)
        w.setSortingEnabled(False)
        w.setItemDelegate(CoopLeaderboardItemDelegate(self))
        self.leaderBoard.setVisible(True)

    def busy_entered(self):
        if not self.loaded:
            self.coop_api.request_coop_scenarios()

    def ask_leaderboard(self) -> None:
        """
        ask the API for stats
        """
        if not self.selectedItem:
            return

        if (player_count := self.tabLeaderWidget.currentIndex()) == 0:
            self.coop_result_api.request_coop_results_general(self.selectedItem.uid)
        else:
            self.coop_result_api.request_coop_results(self.selectedItem.uid, player_count)
        self.tabLeaderWidget.setEnabled(False)

    def coop_list_clicked(self, item: CoopMapItem) -> None:
        """
        Hosting a coop event
        """
        if not hasattr(item, "mapname"):
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
            return

        if item != self.selectedItem:
            self.selectedItem = item
            self.ask_leaderboard()

    def coop_list_double_clicked(self, item: CoopMapItem) -> None:
        """
        Hosting a coop event
        """
        if not hasattr(item, "mapname"):
            return

        if not fa.instance.available():
            return

        self.client.games.stopSearch()

        self._game_launcher.host_game(item.name, "coop", item.mapname)

    @QtCore.pyqtSlot(dict)
    def process_coop_info(self, message: dict[str, list[CoopScenario]]) -> None:
        """
        Slot that interprets coop data from API into the coop list
        """
        for campaign in message["values"]:
            type_coop = campaign.name

            if type_coop not in self.cooptypes:
                root_item = QtWidgets.QTreeWidgetItem()
                self.coopList.addTopLevelItem(root_item)
                root_item.setText(0, f"<font color='white' size=+3>{type_coop}</font>")
                root_item.setToolTip(0, campaign.description)
                self.cooptypes[type_coop] = root_item
                root_item.setExpanded(False)
            else:
                root_item = self.cooptypes[type_coop]

            for mission in campaign.maps:
                item_coop = CoopMapItem(mission.xd, self)
                item_coop.update(mission)
                root_item.addChild(item_coop)

            self.coop[mission.xd] = item_coop
        self.loaded = True

    def game_double_clicked(self, game: Game) -> None:
        """
        Slot that attempts to join a game.
        """
        if not fa.instance.available():
            return

        self.client.games.stopSearch()

        if not fa.check.check(game.featured_mod, game.mapname, sim_mods=game.sim_mods):
            return

        if game.password_protected:
            passw, ok = QtWidgets.QInputDialog.getText(
                self.client, "Passworded game", "Enter password :",
                QtWidgets.QLineEdit.Normal, "",
            )
            if ok:
                self.client.join_game(uid=game.uid, password=passw)
        else:
            self.client.join_game(uid=game.uid)
