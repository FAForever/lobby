from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtCore
from PyQt6 import QtWidgets

import util
from api.player_api import PlayerApiConnector
from api.stats_api import LeaderboardRatingApiConnector
from config import Settings

from .itemviews.leaderboarditemdelegate import LeaderboardItemDelegate
from .models.leaderboardfiltermodel import LeaderboardFilterModel
from .models.leaderboardtablemodel import LeaderboardTableModel

if TYPE_CHECKING:
    from client._clientwindow import ClientWindow

FormClass, BaseClass = util.THEME.loadUiType("stats/leaderboard.ui")

DATE_FORMAT = QtCore.Qt.DateFormat.ISODate


class LeaderboardWidget(BaseClass, FormClass):

    def __init__(
            self,
            client: ClientWindow,
            parent: QtWidgets.QWidget,
            leaderboardName: str,
            *args,
            **kwargs,
    ) -> None:
        super(BaseClass, self).__init__()

        self.setupUi(self)

        self.model = None

        self.client = client
        self.parent = parent
        self.leaderboardName = leaderboardName
        self.apiConnector = LeaderboardRatingApiConnector(self.leaderboardName)
        self.apiConnector.data_ready.connect(self.process_rating_info)
        self.playerApiConnector = PlayerApiConnector()
        self.onlyActive = True
        self.pageNumber = 1
        self.totalPages = 1
        self.pageSize = 1000
        self.query = dict(
            include="player,leaderboard",
            sort="-rating",
            filter=self.prepareFilters(),
        )

        self.onlyActiveCheckBox.stateChanged.connect(
            self.onlyActiveCheckBoxChange,
        )
        self.onlyActiveCheckBox.setChecked(True)

        self.nextButton.clicked.connect(
            lambda: self.getPage(self.pageNumber + 1),
        )
        self.previousButton.clicked.connect(
            lambda: self.getPage(self.pageNumber - 1),
        )
        self.lastButton.clicked.connect(lambda: self.getPage(self.totalPages))
        self.firstButton.clicked.connect(lambda: self.getPage(1))
        self.goToPageButton.clicked.connect(
            lambda: self.getPage(self.pageBox.value()),
        )
        self.pageBox.setValue(self.pageNumber)
        self.pageBox.valueChanged.connect(self.checkTotalPages)
        self.refreshButton.clicked.connect(self.refreshLeaderboard)

        self.findInPageLine.textChanged.connect(self.findEntry)
        self.findInPageLine.returnPressed.connect(
            lambda: self.findEntry(self.findInPageLine.text()),
        )

        self.searchPlayerLine.textEdited.connect(self.searchPlayer)
        self.searchPlayerLine.returnPressed.connect(
            self.searchPlayerInLeaderboard,
        )
        self.searchPlayerButton.clicked.connect(self.searchPlayerInLeaderboard)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.resetLoading)

        self.loading = False

        self.showColumnCheckBoxes = [
            self.showName,
            self.showRating,
            self.showMean,
            self.showDeviation,
            self.showGames,
            self.showWon,
            self.showWinRate,
            self.showUpdated,
        ]

        self.shownColumns = Settings.get(
            "leaderboards/shownColumns",
            default=[True for i in range(len(self.showColumnCheckBoxes))],
            type=bool,
        )

        self.showAllColumns = Settings.get(
            "leaderboards/showAllColumns",
            default=True,
            type=bool,
        )

        self.showAllCheckBox.setChecked(self.showAllColumns)
        self.showAllCheckBox.stateChanged.connect(self.showAllCheckBoxChange)

        for index, checkbox in enumerate(self.showColumnCheckBoxes):
            if self.showAllColumns:
                checkbox.setChecked(False)
                checkbox.setEnabled(False)
            else:
                checkbox.setChecked(self.shownColumns[index])
                checkbox.setEnabled(True)
            checkbox.stateChanged.connect(self.setShownColumns)

        self.tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch,
        )
        self.tableView.horizontalHeader().setFixedHeight(30)
        self.tableView.horizontalHeader().setHighlightSections(False)
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.tableView.horizontalHeader().setSectionsMovable(True)

    def showAllCheckBoxChange(self, state):
        self.showAllColumns = True if state else False
        Settings.set("leaderboards/showAllColumns", self.showAllColumns)
        self.showColumns()

    def setShownColumns(self):
        for i in range(len(self.showColumnCheckBoxes)):
            self.shownColumns[i] = self.showColumnCheckBoxes[i].isChecked()
        Settings.set("leaderboards/shownColumns", self.shownColumns)
        self.showColumns()

    def showColumns(self):
        self.tableView.setColumnHidden(8, True)

        self.showAllCheckBox.blockSignals(True)
        self.showAllCheckBox.setChecked(self.showAllColumns)
        self.showAllCheckBox.blockSignals(False)

        for index, isShown in enumerate(self.shownColumns):
            self.showColumnCheckBoxes[index].blockSignals(True)

            if self.showAllColumns:
                self.tableView.setColumnHidden(index, False)
                self.showColumnCheckBoxes[index].setChecked(False)
                self.showColumnCheckBoxes[index].setEnabled(False)
            else:
                self.tableView.setColumnHidden(index, not isShown)
                self.showColumnCheckBoxes[index].setEnabled(True)
                self.showColumnCheckBoxes[index].setChecked(isShown)

            self.showColumnCheckBoxes[index].blockSignals(False)

    def process_rating_info(self, message: dict) -> None:
        if message["leaderboard"] == self.leaderboardName:
            self.createLeaderboard(message)
            self.processMeta(message["meta"])
            self.resetLoading()
            self.timer.stop()

    def createLeaderboard(self, data):
        self.model = LeaderboardTableModel(data)
        self.findInPageLine.set_completion_list(self.model.logins)
        proxyModel = LeaderboardFilterModel(self.model)
        proxyModel.setSourceModel(self.model)
        self.tableView.verticalHeader().setModel(proxyModel)
        self.tableView.setModel(proxyModel)
        self.tableView.setItemDelegate(LeaderboardItemDelegate(self))

        completer = QtWidgets.QCompleter(
            sorted(self.model.logins, key=lambda login: login.lower()),
        )
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.popup().setStyleSheet(
            "background: rgb(32, 32, 37); color: orange;",
        )
        self.findInPageLine.setCompleter(completer)

        self.showColumns()

    def processMeta(self, meta):
        totalPages = meta["page"]["totalPages"]
        self.totalPages = totalPages if totalPages > 0 else 1
        self.labelTotalPages.setText(str(self.totalPages))

        pageNumber = meta["page"]["number"]
        self.pageNumber = pageNumber if pageNumber > 0 else 1
        self.pageBox.setValue(self.pageNumber)

    def resetLoading(self):
        self.loading = False
        self.labelLoading.clear()

    def findEntry(self, text):
        if self.model is not None:
            for row in self.model.logins:
                if row.lower() == text.lower():
                    self.tableView.selectRow(self.model.logins.index(row))
                    break

    def searchPlayer(self) -> None:
        query = {
            "filter": 'login=="{}*"'.format(self.searchPlayerLine.text()),
            "page[size]": 10,
        }
        self.playerApiConnector.get_by_query(query, self.createPlayerCompleter)

    def createPlayerCompleter(self, message: dict) -> None:
        logins = [player["login"] for player in message["data"]]
        self.searchPlayerLine.set_completion_list(logins)
        completer = QtWidgets.QCompleter(
            sorted(logins, key=lambda login: login.lower()),
        )
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.popup().setStyleSheet(
            "background: rgb(32, 32, 37); color: orange;",
        )
        self.searchPlayerLine.setCompleter(completer)
        completer.complete()

    def onlyActiveCheckBoxChange(self, state):
        self.onlyActive = state
        if state:
            self.dateEditStart.setEnabled(False)
            self.dateEditEnd.setEnabled(False)
        else:
            self.dateEditStart.setEnabled(True)
            self.dateEditEnd.setEnabled(True)

            date = QtCore.QDate.currentDate()
            self.dateEditStart.setDate(date)
            self.dateEditEnd.setDate(date)

    def prepareFilters(self):
        filters = [
            'leaderboard.technicalName=="{}"'.format(self.leaderboardName),
        ]

        if self.onlyActive:
            filters.append(
                'updateTime=ge="{}"'.format(
                    QtCore.QDateTime
                    .currentDateTimeUtc()
                    .addMonths(-1)
                    .toString(DATE_FORMAT),
                ),
            )
        else:
            filters.append(
                'updateTime=ge="{}"'.format(
                    self.dateEditStart
                    .dateTime()
                    .toUTC()
                    .toString(DATE_FORMAT),
                ),
            )
            filters.append(
                'updateTime=le="{}"'.format(
                    self.dateEditEnd
                    .dateTime()
                    .toUTC()
                    .toString(DATE_FORMAT),
                ),
            )

        return "({})".format(";".join(filters))

    def refreshLeaderboard(self):
        self.findInPageLine.clear()
        self.searchPlayerLine.clear()
        self.pageSize = self.quantityBox.value()
        self.query["filter"] = self.prepareFilters()
        self.getPage(1)

    def searchPlayerInLeaderboard(self, player=None):
        filters = [
            'leaderboard.technicalName=="{}"'.format(self.leaderboardName),
        ]
        if player:
            self.searchPlayerLine.setText(player.login)
        if self.searchPlayerLine.text() != "":
            filters.append(
                'player.login=="{}"'.format(self.searchPlayerLine.text()),
            )
            self.query["filter"] = "({})".format(";".join(filters))
            self.getPage(1)

    def checkTotalPages(self):
        if self.pageBox.value() > self.totalPages:
            self.pageBox.setValue(self.totalPages)

    def getPage(self, number):
        if self.loading:
            QtWidgets.QMessageBox.critical(
                self.client,
                "Leaderboards",
                "Please, wait for previous request to finish.",
            )
            return

        if 1 <= number <= self.totalPages:
            self.query["page[size]"] = self.pageSize
            self.query["page[number]"] = number
            self.query["page[totals]"] = "yes"

            self.apiConnector.requestData(self.query)
            self.labelLoading.setText("Loading...")
            self.loading = True
            self.timer.start(40000)

    def entered(self):
        if self.model is None and not self.loading:
            self.getPage(1)

        self.shownColumns = Settings.get(
            "leaderboards/shownColumns",
            default=[True for i in range(len(self.showColumnCheckBoxes))],
            type=bool,
        )
        self.showAllColumns = Settings.get(
            "leaderboards/showAllColumns",
            default=True,
            type=bool,
        )

        self.showColumns()
