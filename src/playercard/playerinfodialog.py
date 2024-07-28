from __future__ import annotations

from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem

import util
from api.models.AvatarAssignment import AvatarAssignment
from api.models.LeaderboardRating import LeaderboardRating
from api.models.NameRecord import NameRecord
from api.models.Player import Player
from api.models.PlayerEvent import PlayerEvent
from api.player_api import PlayerApiConnector
from api.stats_api import LeaderboardRatingApiConnector
from api.stats_api import LeagueSeasonScoreApiConnector
from api.stats_api import PlayerEventApiAccessor
from downloadManager import AvatarDownloader
from playercard.avatarhandler import AvatarHandler
from playercard.leagueformatter import league_formatter_factory
from playercard.ratingtabwidget import RatingTabWidgetController
from playercard.statistics import StatsCharts

FormClass, BaseClass = util.THEME.loadUiType("player_card/playercard.ui")


class PlayerInfoDialog(FormClass, BaseClass):
    def __init__(self, avatar_dler: AvatarDownloader, player_id: str) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.tab_widget_ctrl = RatingTabWidgetController(player_id, self.tabWidget)
        self.avatar_handler = AvatarHandler(self.avatarList, avatar_dler)

        self.player_id = player_id

        self.player_api = PlayerApiConnector()
        self.player_api.player_ready.connect(self.process_player)

        self.leagues_api = LeagueSeasonScoreApiConnector()

        self.ratings_api = LeaderboardRatingApiConnector()
        self.ratings_api.player_ratings_ready.connect(self.process_player_ratings)

        self.player_event_api = PlayerEventApiAccessor()
        self.player_event_api.events_ready.connect(self.process_player_events)

        self.stats_charts = StatsCharts()

    def load_stylesheet(self) -> None:
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def run(self) -> None:
        self.ratings_api.get_player_ratings(self.player_id)
        self.player_api.request_player(self.player_id)
        self.player_event_api.get_player_events(self.player_id)
        self.tab_widget_ctrl.run()
        self.exec()

    def process_player_ratings(self, ratings: dict[str, list[LeaderboardRating]]) -> None:
        for rating in ratings["values"]:
            widget = league_formatter_factory(self.player_id, rating, self.leagues_api)
            self.leaguesLayout.addWidget(widget)
        pie_chart = self.stats_charts.game_types_played(ratings["values"])
        self.statsChartsLayout.addWidget(pie_chart)

    def process_player(self, player: Player) -> None:
        self.nicknameLabel.setText(player.login)
        self.idLabel.setText(player.xd)
        registered = QDateTime.fromString(player.create_time, Qt.DateFormat.ISODate).toLocalTime()
        self.registeredLabel.setText(registered.toString("yyyy-MM-dd hh:mm"))
        last_login = QDateTime.fromString(player.update_time, Qt.DateFormat.ISODate).toLocalTime()
        self.lastLoginLabel.setText(last_login.toString("yyyy-MM-dd hh:mm"))
        self.add_avatars(player.avatar_assignments)
        self.add_names(player.names)

    def add_names(self, names: list[NameRecord] | None) -> None:
        if names is None:
            return
        self.nameHistoryTableWidget.setRowCount(len(names))
        for row, name_record in enumerate(names):
            name = QTableWidgetItem(name_record.name)
            change_time = QDateTime.fromString(name_record.change_time, Qt.DateFormat.ISODate)
            used_until = QTableWidgetItem(change_time.toString("yyyy-MM-dd hh:mm"))
            self.nameHistoryTableWidget.setItem(row, 0, name)
            self.nameHistoryTableWidget.setItem(row, 1, used_until)

    def add_avatars(self, avatar_assignments: list[AvatarAssignment] | None) -> None:
        self.avatar_handler.populate_avatars(avatar_assignments)

    def process_player_events(self, events: list[PlayerEvent]) -> None:
        for chartview in self.stats_charts.player_events_charts(events):
            self.statsChartsLayout.addWidget(chartview)
