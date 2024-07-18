from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence
from typing import TYPE_CHECKING

import pyqtgraph as pg
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QPointF
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QListWidget
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QTabWidget
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

import util
from api.models.Avatar import Avatar
from api.models.AvatarAssignment import AvatarAssignment
from api.models.Leaderboard import Leaderboard
from api.models.LeaderboardRating import LeaderboardRating
from api.models.LeaderboardRatingJournal import LeaderboardRatingJournal
from api.models.NameRecord import NameRecord
from api.models.Player import Player
from api.models.PlayerEvent import PlayerEvent
from api.player_api import PlayerApiConnector
from api.stats_api import LeaderboardApiConnector
from api.stats_api import LeaderboardRatingApiConnector
from api.stats_api import LeaderboardRatingJournalApiConnector
from api.stats_api import LeagueSeasonScoreApiConnector
from api.stats_api import PlayerEventApiAccessor
from downloadManager import AvatarDownloader
from downloadManager import DownloadRequest
from model.rating import Rating
from playercard.statistics import StatsCharts
from src.playercard.leagueformatter import LegueFormatter

if TYPE_CHECKING:
    from client._clientwindow import ClientWindow

FormClass, BaseClass = util.THEME.loadUiType("player_card/playercard.ui")

Numeric = float | int


class Crosshairs:
    def __init__(self, plotwidget: pg.PlotWidget, series: LineSeries) -> None:
        self.plotwidget = plotwidget
        self.plotwidget.scene().sigMouseMoved.connect(self.update_lines_and_text)

        self.series = series

        pen = pg.mkPen("green", width=3)
        self.xLine = pg.InfiniteLine(angle=90, pen=pen)
        self.yLine = pg.InfiniteLine(angle=0, pen=pen)

        self.plotwidget.addItem(self.xLine, ignoreBounds=True)
        self.plotwidget.addItem(self.yLine, ignoreBounds=True)

        color = QColor("black")
        self.xText = pg.TextItem(color=color)
        self.yText = pg.TextItem(color=color)

        self.plotwidget.scene().addItem(self.xText)
        self.plotwidget.scene().addItem(self.yText)

        self.plotwidget.plotItem.getAxis("left").setWidth(40)
        self._visible = True

    def set_series(self, series: LineSeries) -> None:
        self.series = series

    def set_visible(self, visible: bool) -> None:
        self.xLine.setVisible(visible)
        self.yLine.setVisible(visible)
        self.xText.setVisible(visible)
        self.yText.setVisible(visible)

    def display(self, *, seen: bool) -> None:
        if not self._visible:
            return
        self.set_visible(seen)

    def hide(self) -> None:
        self.set_visible(False)

    def show(self) -> None:
        self.set_visible(True)

    def change_visibility(self) -> None:
        new_state = not self._visible
        self.set_visible(new_state)
        self._visible = new_state

    def is_visible(self) -> bool:
        return self._visible

    def _closest_index(self, lst: Sequence[Numeric], value: Numeric) -> int:
        pos = bisect_left(lst, value)
        if pos == 0:
            return pos
        if pos == len(lst):
            return pos - 1

        before = lst[pos - 1]
        after = lst[pos]
        if after - value < value - before:
            return pos
        else:
            return pos - 1

    def map_to_data(self, pos: QPointF) -> QPointF:
        view = self.plotwidget.plotItem.getViewBox()
        value_pos = view.mapSceneToView(pos)
        point_index = self._closest_index(self.series.x(), value_pos.x())
        return self.series.point_at(point_index)

    def get_xtext_pos(self, scene_point: QPointF) -> tuple[float, float]:
        scene_width = self.plotwidget.sceneBoundingRect().width()
        text_width = self.xText.boundingRect().width()
        text_height = self.xText.boundingRect().height()
        padding = 3

        left_margin = self.plotwidget.plotItem.getAxis("left").width() - padding
        right_margin = scene_width - text_width + padding

        x = max(left_margin, scene_point.x() - text_width / 2)
        x = min(x, right_margin)
        y = self.plotwidget.sceneBoundingRect().bottom() - text_height + padding
        return x, y

    def get_ytext_pos(self, scene_point: QPointF) -> tuple[float, float]:
        padding = 3
        x = self.plotwidget.sceneBoundingRect().left() - padding
        y = scene_point.y() - self.yText.boundingRect().height() / 2
        return x, y

    def update_lines_and_text(self, pos: QPointF) -> None:
        if not self.series.x():
            return

        data_point = self.map_to_data(pos)
        view = self.plotwidget.plotItem.getViewBox()
        scene_point = view.mapViewToScene(data_point)

        left_margin = self.plotwidget.plotItem.getAxis("left").width()
        if scene_point.x() < left_margin or scene_point.y() < 0:
            return

        self.update_lines(pos, data_point)
        self.update_text(scene_point, data_point)
        self.show_at_pos(scene_point)

    def update_text(self, scene_point: QPointF, data_point: QPointF) -> None:
        date = QDateTime.fromSecsSinceEpoch(round(data_point.x())).toString("dd-MM-yyyy hh:mm")
        self.xText.setHtml(f"<div style='background-color: #ffff00;'>{date}</div>")
        self.xText.setPos(*self.get_xtext_pos(scene_point))
        self.yText.setHtml(f"<div style='background-color: #ffff00;'>{data_point.y():.2f}</div>")
        self.yText.setPos(*self.get_ytext_pos(scene_point))

    def update_lines(self, pos: QPointF, data_point: QPointF) -> None:
        if self.plotwidget.sceneBoundingRect().contains(pos):
            self.xLine.setPos(data_point.x())
            self.yLine.setPos(data_point.y())

    def show_at_pos(self, pos: QPointF) -> None:
        seen = self.plotwidget.sceneBoundingRect().contains(pos)
        self.display(seen=seen)


class PlayerInfoDialog(FormClass, BaseClass):
    def __init__(self, client_window: ClientWindow, player_id: str) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.tab_widget_ctrl = RatingTabWidgetController(player_id, self.tabWidget)
        self.avatar_handler = AvatarHandler(self.avatarList, client_window.avatar_downloader)

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
            self.leaguesLayout.addWidget(LegueFormatter(self.player_id, rating, self.leagues_api))
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


class AvatarHandler:
    def __init__(self, avatar_list: QListWidget, avatar_downloader: AvatarDownloader) -> None:
        self.avatar_list = avatar_list
        self.avatar_dler = avatar_downloader
        self.requests = {}

    def populate_avatars(self, avatar_assignments: list[AvatarAssignment] | None) -> None:
        if avatar_assignments is None:
            return

        for assignment in avatar_assignments:
            if self.avatar_dler.has_avatar(assignment.avatar.filename):
                self._add_avatar(assignment.avatar)
            else:
                self._download_avatar(assignment.avatar)

    def _prepare_avatar_dl_request(self, avatar: Avatar) -> DownloadRequest:
        req = DownloadRequest()
        req.done.connect(self._handle_avatar_download)
        self.requests[avatar.url] = (req, avatar.tooltip)
        return req

    def _download_avatar(self, avatar: Avatar) -> None:
        req = self._prepare_avatar_dl_request(avatar)
        self.avatar_dler.download_avatar(avatar.url, req)

    def _add_avatar(self, avatar: Avatar) -> None:
        self._add_avatar_item(self.avatar_dler.get_avatar(avatar.filename), avatar.tooltip)

    def _add_avatar_item(self, pixmap: QPixmap, description: str) -> None:
        if pixmap.isNull():
            icon = util.THEME.icon("chat/avatar/avatar_blank.png")
        else:
            icon = QIcon(pixmap.scaled(40, 20))
        avatar_item = QListWidgetItem(icon, description)
        self.avatar_list.addItem(avatar_item)

    def _handle_avatar_download(self, url: str, pixmap: QPixmap) -> None:
        _, tooltip = self.requests[url]
        self._add_avatar_item(pixmap, tooltip)
        del self.requests[url]


class LineSeries:
    def __init__(self) -> None:
        self._x: list[Numeric] = []
        self._y: list[Numeric] = []

    def x(self) -> list[Numeric]:
        return self._x

    def y(self) -> list[Numeric]:
        return self._y

    def append(self, x: Numeric, y: Numeric) -> None:
        self._x.append(x)
        self._y.append(y)

    def point_at(self, index: int) -> QPointF:
        return QPointF(self._x[index], self._y[index])


class RatingsPlotTab(QObject):
    name_changed = pyqtSignal(int, str)

    def __init__(
            self,
            index: int,
            player_id: str,
            leaderboard: Leaderboard,
            plot: PlotController,
    ) -> None:
        super().__init__()
        self.index = index
        self.player_id = player_id
        self.leaderboard = leaderboard
        self.ratings_history_api = LeaderboardRatingJournalApiConnector()
        self.ratings_history_api.ratings_ready.connect(self.process_rating_history)
        self.plot = plot
        self._loaded = False

    def enter(self) -> None:
        if self._loaded:
            return
        self.name_changed.emit(self.index, "Loading...")
        self.ratings_history_api.get_full_history(self.player_id, self.leaderboard.technical_name)

    def get_plot_series(self, ratings: list[LeaderboardRatingJournal]) -> LineSeries:
        series = LineSeries()
        for entry in ratings:
            assert entry.player_stats is not None
            score_time = QDateTime.fromString(entry.player_stats.score_time, Qt.DateFormat.ISODate)
            series.append(
                score_time.toSecsSinceEpoch(),
                Rating(entry.mean_after, entry.deviation_after).displayed(),
            )
        return series

    def process_rating_history(self, ratings: dict[str, list[LeaderboardRatingJournal]]) -> None:
        self.plot.draw_series(self.get_plot_series(ratings["values"]))
        self._loaded = True
        self.name_changed.emit(self.index, self.leaderboard.pretty_name)


class RatingTabWidgetController:
    def __init__(self, player_id: str, tab_widget: QTabWidget) -> None:
        self.player_id = player_id
        self.widget = tab_widget
        self.widget.currentChanged.connect(self.on_tab_changed)

        self.leaderboards_api = LeaderboardApiConnector()
        self.leaderboards_api.data_ready.connect(self.populate_leaderboards)
        self.tabs: dict[int, RatingsPlotTab] = {}

    def run(self) -> None:
        self.leaderboards_api.requestData()

    def populate_leaderboards(self, message: dict[str, list[Leaderboard]]) -> None:
        for index, leaderboard in enumerate(message["values"]):
            widget = pg.PlotWidget()
            tab = RatingsPlotTab(index, self.player_id, leaderboard, PlotController(widget))
            tab.name_changed.connect(self.widget.setTabText)
            self.tabs[index] = tab
            self.widget.insertTab(index, widget, leaderboard.pretty_name)

    def on_tab_changed(self, index: int) -> None:
        self.tabs[index].enter()


class PlotController:
    def __init__(self, widget: pg.PlotWidget) -> None:
        self.widget = widget
        self.widget.setBackground("#202025")
        self.widget.setAxisItems({"bottom": DateAxisItem()})
        self.crosshairs = Crosshairs(self.widget, LineSeries())
        self.hide_irrelevant_plot_actions()
        self.add_custom_menu_actions()

    def clear(self) -> None:
        self.widget.clear()

    def draw_series(self, series: LineSeries) -> None:
        self.widget.plot(series.x(), series.y(), pen=pg.mkPen("orange"))
        self.crosshairs.set_series(series)
        self.widget.autoRange()

    def hide_irrelevant_plot_actions(self) -> None:
        for action in ("Transforms", "Downsample", "Average", "Alpha", "Points"):
            self.widget.plotItem.setContextMenuActionVisible(action, visible=False)

    def add_custom_menu_actions(self) -> None:
        viewbox = self.widget.plotItem.getViewBox()
        if viewbox is None:
            return

        menu = viewbox.getMenu(ev=None)
        if menu is None:
            return

        menu.addAction("Show/Hide crosshair", self.crosshairs.change_visibility)
