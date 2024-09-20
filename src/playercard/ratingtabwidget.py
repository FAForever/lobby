from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QPointF
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget

from src.api.models.Leaderboard import Leaderboard
from src.api.stats_api import LeaderboardApiConnector
from src.api.stats_api import LeaderboardRatingJournalApiConnector
from src.model.rating import Rating
from src.playercard.plot import LineSeries
from src.playercard.plot import PlotController


class LineSeriesParser(QThread):
    result_ready = pyqtSignal(LineSeries)

    def __init__(self, unparsed_api_response: dict) -> None:
        QThread.__init__(self)
        self.data = unparsed_api_response

    def run(self) -> None:
        self.parse()

    def parse(self) -> None:
        journal = self.data["data"]
        journal_leng = len(journal)

        if journal_leng == 0:
            self.result_ready.emit(LineSeries())
            return

        stats = self.data["included"]
        stats_leng = len(stats)

        series = LineSeries(stats_leng)

        stats_index = journal_index = 0
        while stats_index < stats_leng and journal_index < journal_leng:
            if (
                stats[stats_index]["id"]
                != journal[journal_index]["relationships"]["gamePlayerStats"]["data"]["id"]
            ):
                journal_index += 1
                continue

            score_time_str = stats[stats_index]["attributes"]["scoreTime"]
            score_time = QDateTime.fromString(score_time_str, Qt.DateFormat.ISODate)
            # not creating additional objects (like Rating and QPointF)
            # and not accessing their attributes in a loop will also give small
            # improvement, but not quite noticeable (a few hundreds of a second
            # per 10000 loop cycles -- ~10x less than API call deviation)
            rating = Rating(
                journal[journal_index]["attributes"]["meanAfter"],
                journal[journal_index]["attributes"]["deviationAfter"],
            )
            point = QPointF(
                score_time.toSecsSinceEpoch(),
                rating.displayed(),
            )
            series.set_point(stats_index, point)
            stats_index += 1
            journal_index += 1

        self.result_ready.emit(series)


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
        self.workers = []

    def __del__(self) -> None:
        try:
            self.clear_threads()
        except RuntimeError:
            pass

    def enter(self) -> None:
        if self._loaded:
            return
        self.name_changed.emit(self.index, "Loading...")
        self.ratings_history_api.get_full_history(self.player_id, self.leaderboard.technical_name)

    def clear_threads(self) -> None:
        for worker in self.workers:
            if worker.isRunning():
                worker.quit()
        self.workers.clear()

    def finish(self) -> None:
        self.clear_threads()
        self.plot.draw_series()
        self.name_changed.emit(self.index, self.leaderboard.pretty_name)

    def process_rating_history(self, message: dict) -> None:
        total_pages = message["meta"]["page"]["totalPages"]
        current_page = message["meta"]["page"]["number"]
        self._loaded = current_page >= total_pages

        worker = LineSeriesParser(message)
        self.workers.append(worker)
        worker.result_ready.connect(self.data_parsed)
        worker.start()

    def data_parsed(self, series: LineSeries) -> None:
        self.plot.add_data(series)
        if self._loaded:
            self.finish()


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
