from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence
from typing import TYPE_CHECKING

import pyqtgraph as pg
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QPointF
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QListWidget
from PyQt6.QtWidgets import QListWidgetItem
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

import util
from api.models.Avatar import Avatar
from api.models.AvatarAssignment import AvatarAssignment
from api.models.Leaderboard import Leaderboard
from api.models.LeaderboardRating import LeaderboardRating
from api.models.LeaderboardRatingJournal import LeaderboardRatingJournal
from api.models.Player import Player
from api.player_api import PlayerApiConnector
from api.stats_api import LeaderboardApiConnector
from api.stats_api import LeaderboardRatingApiConnector
from api.stats_api import LeaderboardRatingJournalApiConnector
from api.stats_api import LeagueSeasonScoreApiConnector
from downloadManager import AvatarDownloader
from downloadManager import DownloadRequest
from src.playercard.leagueformatter import LegueFormatter

if TYPE_CHECKING:
    from client._clientwindow import ClientWindow

FormClass, BaseClass = util.THEME.loadUiType("player_card/playercard.ui")


class Crosshairs:
    def __init__(self, plotwidget: pg.PlotWidget, xseries: list[int], yseries: list[float]) -> None:
        self.plotwidget = plotwidget
        self.plotwidget.scene().sigMouseMoved.connect(self.update_lines_and_text)

        self.xseries = xseries
        self.yseries = yseries

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

    def set_visible(self, visible: bool) -> None:
        self.xLine.setVisible(visible)
        self.yLine.setVisible(visible)
        self.xText.setVisible(visible)
        self.yText.setVisible(visible)
        self._visible = visible

    def hide(self) -> None:
        self.set_visible(False)

    def show(self) -> None:
        self.set_visible(True)

    def change_visibility(self) -> None:
        self.set_visible(not self._visible)

    def is_visible(self) -> bool:
        return self._visible

    def _closest_index(self, lst: Sequence[float | int], value: float | int) -> int:
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
        point_index = self._closest_index(self.xseries, value_pos.x())
        return QPointF(self.xseries[point_index], self.yseries[point_index])

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
        if not self.xseries:
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
        self.set_visible(seen)


class PlayerInfoDialog(FormClass, BaseClass):
    def __init__(self, client_window: ClientWindow, player_id: str) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.avatar_handler = AvatarHandler(self.avatarList, client_window.avatar_downloader)

        self.player_id = player_id

        self.player_api = PlayerApiConnector()
        self.player_api.player_ready.connect(self.process_player)

        self.leaderboards_api = LeaderboardApiConnector()
        self.leaderboards_api.data_ready.connect(self.populate_leaderboards)

        self.ratings_history_api = LeaderboardRatingJournalApiConnector()
        self.ratings_history_api.ratings_ready.connect(self.process_rating_history)

        self.plotWidget.setBackground("#202025")
        self.plotWidget.setAxisItems({"bottom": DateAxisItem()})

        self.ratingComboBox.currentTextChanged.connect(self.get_ratings)
        self.crosshairs = None

        self.leagues_api = LeagueSeasonScoreApiConnector()

        self.ratings_api = LeaderboardRatingApiConnector()
        self.ratings_api.player_ratings_ready.connect(self.process_player_ratings)
        self.ratings_api.get_player_ratings(self.player_id)

    def load_stylesheet(self) -> None:
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def run(self) -> None:
        self.leaderboards_api.requestData()
        self.player_api.request_player(self.player_id)
        self.exec()

    def populate_leaderboards(self, message: dict[str, list[Leaderboard]]) -> None:
        for leaderboard in message["values"]:
            self.ratingComboBox.addItem(leaderboard.technical_name)

    def clear_graphics(self) -> None:
        self.plotWidget.clear()
        if self.crosshairs is not None:
            self.crosshairs.hide()
            self.crosshairs = None

    def get_ratings(self, leaderboard_name: str) -> None:
        self.ratingComboBox.setEnabled(False)
        self.ratings_history_api.get_full_history(self.player_id, leaderboard_name)

    def get_chart_series(self, ratings: list[LeaderboardRatingJournal]) -> tuple[list, list]:
        xvals, yvals = [], []
        for entry in ratings:
            assert entry.player_stats is not None
            score_time = QDateTime.fromString(entry.player_stats.score_time, Qt.DateFormat.ISODate)
            xvals.append(score_time.toSecsSinceEpoch())
            yvals.append(entry.mean_after - 3 * entry.deviation_after)
        return xvals, yvals

    def draw_ratings(self, ratings: tuple[list, list]) -> None:
        self.plotWidget.plot(*ratings, pen=pg.mkPen("orange"))
        self.crosshairs = Crosshairs(self.plotWidget, *ratings)
        self.plotWidget.autoRange()

    def process_rating_history(self, ratings: dict[str, list[LeaderboardRatingJournal]]) -> None:
        self.clear_graphics()
        self.draw_ratings(self.get_chart_series(ratings["values"]))
        self.ratingComboBox.setEnabled(True)

    def process_player_ratings(self, ratings: dict[str, list[LeaderboardRating]]) -> None:
        for rating in ratings["values"]:
            self.leaguesLayout.addWidget(LegueFormatter(self.player_id, rating, self.leagues_api))

    def process_player(self, player: Player) -> None:
        self.nicknameLabel.setText(player.login)
        self.idLabel.setText(player.xd)
        registered = QDateTime.fromString(player.create_time, Qt.DateFormat.ISODate).toLocalTime()
        self.registeredLabel.setText(registered.toString("yyyy-MM-dd hh:mm"))
        last_login = QDateTime.fromString(player.update_time, Qt.DateFormat.ISODate).toLocalTime()
        self.lastLoginLabel.setText(last_login.toString("yyyy-MM-dd hh:mm"))
        self.add_avatars(player.avatar_assignments)

    def add_avatars(self, avatar_assignments: list[AvatarAssignment] | None) -> None:
        self.avatar_handler.populate_avatars(avatar_assignments)


class AvatarHandler:
    def __init__(self, avatar_list: QListWidget, avatar_downloader: AvatarDownloader) -> None:
        self.avatar_list = avatar_list
        self.avatar_dler = avatar_downloader
        self.requests = {}

    def populate_avatars(self, avatar_assignments: list[AvatarAssignment] | None) -> None:
        if avatar_assignments is None:
            return

        for assignment in avatar_assignments:
            pix = self.avatar_dler.avatars.get(assignment.avatar.filename, None)
            if pix is None:
                self._download_avatar(assignment.avatar)
            else:
                self._add_avatar_item(pix, assignment.avatar.tooltip)

    def _prepare_avatar_dl_request(self, avatar: Avatar) -> DownloadRequest:
        req = DownloadRequest()
        req.done.connect(self._handle_avatar_download)
        self.requests[avatar.url] = (req, avatar.tooltip)
        return req

    def _download_avatar(self, avatar: Avatar) -> None:
        req = self._prepare_avatar_dl_request(avatar)
        self.avatar_dler.download_avatar(avatar.url, req)

    def _add_avatar_item(self, pixmap: QPixmap, description: str) -> None:
        icon = QIcon(pixmap.scaled(40, 20))
        avatar_item = QListWidgetItem(icon, description)
        self.avatar_list.addItem(avatar_item)

    def _handle_avatar_download(self, url: str, pixmap: QPixmap) -> None:
        _, tooltip = self.requests[url]
        self._add_avatar_item(pixmap, tooltip)
        del self.requests[url]
