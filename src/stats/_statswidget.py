import logging
import time

from PyQt6 import QtCore
from PyQt6 import QtWidgets

import util
from api.models.Leaderboard import Leaderboard
from api.stats_api import LeaderboardApiConnector
from ui.busy_widget import BusyWidget

from .leaderboard_widget import LeaderboardWidget

logger = logging.getLogger(__name__)

ANTIFLOOD = 0.1

FormClass, BaseClass = util.THEME.loadUiType("stats/stats.ui")


class StatsWidget(BaseClass, FormClass, BusyWidget):

    # signals
    laddermaplist = QtCore.pyqtSignal(dict)

    def __init__(self, client):
        super(BaseClass, self).__init__()

        self.setupUi(self)

        self.client = client

        self.selected_player = None
        self.selected_player_loaded = False
        self.leagues.currentChanged.connect(self.leagueUpdate)
        self.currentChanged.connect(self.busy_entered)
        self.pagesDivisions = {}
        self.pagesDivisionsResults = {}
        self.pagesAllLeagues = {}

        self.floodtimer = time.time()

        self.currentLeague = 0
        self.currentDivision = 0

        self.FORMATTER_LADDER = str(
            util.THEME.readfile("stats/formatters/ladder.qthtml"),
        )
        self.FORMATTER_LADDER_HEADER = str(
            util.THEME.readfile("stats/formatters/ladder_header.qthtml"),
        )

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        # setup other tabs

        self.apiConnector = LeaderboardApiConnector()
        self.apiConnector.data_ready.connect(self.process_leaderboards_info)
        self.apiConnector.requestData({"sort": "id"})

        # hiding some non-functional tabs
        self.removeTab(self.indexOf(self.ladderTab))
        self.removeTab(self.indexOf(self.laddermapTab))

        self.leaderboardNames = []
        self.client.authorized.connect(self.onAuthorized)

    def onAuthorized(self):
        if not self.leaderboardNames:
            self.refreshLeaderboards()

    def refreshLeaderboards(self):
        while self.client.replays.leaderboardList.count() != 1:
            self.client.replays.leaderboardList.removeItem(1)
        self.leaderboards.blockSignals(True)
        while self.leaderboards.widget(0) is not None:
            self.leaderboards.widget(0).deleteLater()
            self.leaderboards.removeTab(0)
        self.apiConnector.requestData(dict(sort="id"))
        self.leaderboards.blockSignals(False)

    def load_stylesheet(self):
        self.setStyleSheet(
            util.THEME.readstylesheet("stats/formatters/style.css"),
        )

    @QtCore.pyqtSlot(int)
    def leagueUpdate(self, index):
        self.currentLeague = index + 1
        leagueTab = self.leagues.widget(index).findChild(
            QtWidgets.QTabWidget, "league" + str(index),
        )
        if leagueTab:
            if leagueTab.currentIndex() == 0:
                if time.time() - self.floodtimer > ANTIFLOOD:
                    self.floodtimer = time.time()
                    self.client.statsServer.send(
                        dict(
                            command="stats",
                            type="league_table",
                            league=self.currentLeague,
                        ),
                    )

    @QtCore.pyqtSlot(int)
    def divisionsUpdate(self, index):
        if index == 0:
            if time.time() - self.floodtimer > ANTIFLOOD:
                self.floodtimer = time.time()
                self.client.statsServer.send(
                    dict(
                        command="stats",
                        type="league_table",
                        league=self.currentLeague,
                    ),
                )

        elif index == 1:
            tab = self.currentLeague - 1
            if tab not in self.pagesDivisions:
                self.client.statsServer.send(
                    dict(
                        command="stats",
                        type="divisions",
                        league=self.currentLeague,
                    ),
                )

    @QtCore.pyqtSlot(int)
    def divisionUpdate(self, index):
        if time.time() - self.floodtimer > ANTIFLOOD:
            self.floodtimer = time.time()
            self.client.statsServer.send(
                dict(
                    command="stats",
                    type="division_table",
                    league=self.currentLeague,
                    division=index,
                ),
            )

    def createDivisionsTabs(self, divisions):
        userDivision = ""
        me = self.client.me.player
        if me.league is not None:  # was me.division, but no there there
            userDivision = me.league[1]  # ? [0]=league and [1]=division

        pages = QtWidgets.QTabWidget()

        foundDivision = False

        for division in divisions:
            name = division["division"]
            index = division["number"]
            league = division["league"]
            widget = QtWidgets.QTextBrowser()

            if league not in self.pagesDivisionsResults:
                self.pagesDivisionsResults[league] = {}

            self.pagesDivisionsResults[league][index] = widget

            pages.insertTab(index, widget, name)

            if name == userDivision:
                foundDivision = True
                pages.setCurrentIndex(index)
                self.client.statsServer.send(
                    dict(
                        command="stats",
                        type="division_table",
                        league=league,
                        division=index,
                    ),
                )

        if not foundDivision:
            self.client.statsServer.send(
                dict(
                    command="stats",
                    type="division_table",
                    league=league,
                    division=0,
                ),
            )

        pages.currentChanged.connect(self.divisionUpdate)
        return pages

    def createResults(self, values, table):

        formatter = self.FORMATTER_LADDER
        formatter_header = self.FORMATTER_LADDER_HEADER
        glist = []
        append = glist.append
        append(
            "<table style='color:#3D3D3D' cellspacing='0' cellpadding='4' "
            "width='100%' height='100%'><tbody>",
        )
        append(
            formatter_header.format(
                rank="rank", name="name", score="score", color="#92C1E4",
            ),
        )

        for val in values:
            rank = val["rank"]
            name = val["name"]
            score = str(val["score"])
            if self.client.login == name:
                append(
                    formatter.format(
                        rank=str(rank), name=name, score=score, color="#6CF",
                    ),
                )
            elif rank % 2 == 0:
                append(
                    formatter.format(
                        rank=str(rank), name=name,
                        score=str(val["score"]), color="#F1F1F1",
                    ),
                )
            else:
                append(
                    formatter.format(
                        rank=str(rank), name=name,
                        score=str(val["score"]), color="#D8D8D8",
                    ),
                )

        append("</tbody></table>")
        html = "".join(glist)

        table.setHtml(html)

        table.verticalScrollBar().setValue(table.verticalScrollBar().minimum())
        return table

    @QtCore.pyqtSlot(int)
    def leaderboardsTabChanged(self, curr):
        if self.leaderboards.widget(curr) is not None:
            self.leaderboards.widget(curr).entered()

    def process_leaderboards_info(self, message: dict[str, list[Leaderboard]]) -> None:
        self.leaderboardNames.clear()
        for leaderboard in message["values"]:
            self.leaderboardNames.append(leaderboard.technical_name)
        for index, name in enumerate(self.leaderboardNames):
            self.leaderboards.insertTab(
                index,
                LeaderboardWidget(self.client, self, name),
                name.capitalize().replace("_", " "),
            )
            self.client.replays.leaderboardList.addItem(name)
        self.leaderboards.setCurrentIndex(1)
        self.leaderboards.currentChanged.connect(self.leaderboardsTabChanged)

    @QtCore.pyqtSlot()
    def busy_entered(self):
        if self.currentIndex() == self.indexOf(self.leaderboardsTab):
            self.leaderboards.currentChanged.emit(
                self.leaderboards.currentIndex(),
            )
