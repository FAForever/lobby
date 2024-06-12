from bisect import bisect_left

import pyqtgraph as pg
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QPointF
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

import util
from api.models.Leaderboard import Leaderboard
from api.models.LeaderboardRating import LeaderboardRating
from api.models.LeaderboardRatingJournal import LeaderboardRatingJournal
from api.models.LeagueSeasonScore import LeagueSeasonScore
from api.stats_api import LeaderboardApiConnector
from api.stats_api import LeaderboardRatingApiConnector
from api.stats_api import LeaderboardRatingJournalApiConnector
from api.stats_api import LeagueSeasonScoreApiConnector
from client.leagueformatter import LegueFormatter

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

    def _closest_index(self, lst: list[float], value: float) -> int:
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
    def __init__(self, login: str, xd: str) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.player_login = login
        self.player_id = xd

        self.leaderboards_api = LeaderboardApiConnector()
        self.leaderboards_api.data_ready.connect(self.populate_leaderboards)

        self.ratings_history_api = LeaderboardRatingJournalApiConnector()
        self.ratings_history_api.ratings_ready.connect(self.process_rating_history)

        self.plotWidget.setBackground("#202025")
        self.plotWidget.setAxisItems({"bottom": DateAxisItem()})

        self.ratingComboBox.currentTextChanged.connect(self.get_ratings)
        self.crosshairs = None

        self.leagues_api = LeagueSeasonScoreApiConnector()
        self.leagues_api.data_ready.connect(self.on_leagues_ready)

        self.ratings_api = LeaderboardRatingApiConnector()
        self.ratings_api.player_ratings_ready.connect(self.process_player_ratings)
        self.ratings_api.get_player_ratings(self.player_id)

    def load_stylesheet(self) -> None:
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def on_leagues_ready(self, message: dict[str, list[LeagueSeasonScore]]) -> None:
        for score in message["values"]:
            if score.subdivision is None:
                continue

    def run(self) -> None:
        self.leaderboards_api.requestData()
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
