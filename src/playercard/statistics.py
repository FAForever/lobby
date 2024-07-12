from collections.abc import Generator
from typing import Iterable

from PyQt6.QtCharts import QBarCategoryAxis
from PyQt6.QtCharts import QBarSet
from PyQt6.QtCharts import QChart
from PyQt6.QtCharts import QChartView
from PyQt6.QtCharts import QPieSeries
from PyQt6.QtCharts import QStackedBarSeries
from PyQt6.QtCharts import QValueAxis
from PyQt6.QtCore import QMargins
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QPainter

from api.models.LeaderboardRating import LeaderboardRating
from api.models.PlayerEvent import PlayerEvent
from playercard.events import BUILT_LOST_METRICS
from playercard.events import EXPERIMENTALS_BUILT_LOST_METRICS
from playercard.events import FACTION_PLAYS_METRICS
from playercard.events import PlayerEventMetric


class ChartsBuilder:
    def __init__(self) -> None:
        self.background_color = QColor("#202025")
        self.background_brush = QBrush(self.background_color)
        self.chart_content_margins = (0, 0, 0, 0)
        self.chart_margins = QMargins()
        self.background_roundess = 0
        self.title_brush = QBrush(QColor("silver"))
        self.title_size = 12
        self.legend_label_color = QColor("silver")

    def customize_title_font(self, chart: QChart) -> QFont:
        current_font = chart.titleFont()
        current_font.setPointSize(self.title_size)
        return current_font

    def create_customized_chart(self) -> QChart:
        chart = QChart()
        chart.setBackgroundBrush(self.background_brush)
        chart.setTitleBrush(self.title_brush)
        chart.setTitleFont(self.customize_title_font(chart))
        chart.legend().setLabelColor(self.legend_label_color)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.layout().setContentsMargins(*self.chart_content_margins)
        chart.setMargins(self.chart_margins)
        chart.setBackgroundRoundness(self.background_roundess)
        return chart

    def create_chartview(self, chart: QChart) -> QChartView:
        view = QChartView(chart)
        view.setMinimumHeight(500)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return view


class PieChartBuilder(ChartsBuilder):

    def create_series(
            self,
            data: Iterable[tuple[str, int | float]],
    ) -> QPieSeries:
        series = QPieSeries()
        for slice_data in data:
            series.append(*slice_data)
        return series

    def customize_series_labels(self, series: QPieSeries) -> None:
        for pie_slice in series.slices():
            percentage = round(pie_slice.percentage() * 100, 2)
            pie_slice.setLabel(f"{pie_slice.label()} ({percentage}%)")
            pie_slice.setLabelColor(self.legend_label_color)
        series.setLabelsVisible(True)

    def build(
            self,
            title: str,
            data: Iterable[tuple[str, int | float]],
    ) -> QChartView:
        series = self.create_series(data)
        self.customize_series_labels(series)

        chart = self.create_customized_chart()
        chart.addSeries(series)
        chart.setTitle(title)

        return self.create_chartview(chart)


class StackedBarChartBuilder(ChartsBuilder):

    def create_series(
            self,
            set_names: Iterable[str],
            set_values: Iterable[Iterable[int | float]],
    ) -> QStackedBarSeries:
        series = QStackedBarSeries()
        for name, dataset in zip(set_names, set_values):
            barset = QBarSet(name)
            barset.setPen(self.background_color)
            barset.append(dataset)
            series.append(barset)
        return series

    def customize_series_labels(self, series: QStackedBarSeries) -> None:
        series.setLabelsFormat("@value")
        series.setLabelsVisible(True)

    def build(
            self,
            title: str,
            data: Iterable[Iterable[int | float]],
            set_names: Iterable[str],
            categories: Iterable[str],
    ) -> QChartView:
        series = self.create_series(set_names, data)
        self.customize_series_labels(series)

        chart = self.create_customized_chart()
        chart.addSeries(series)
        chart.setTitle(title)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("i")

        for axis in (axis_x, axis_y):
            axis.setLabelsColor(self.legend_label_color)
            axis.setGridLineVisible(False)
            series.attachAxis(axis)

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        return self.create_chartview(chart)


class StatsCharts:

    def bar_chart(
            self,
            title: str,
            set_names: Iterable[str],
            metrics: tuple[PlayerEventMetric, ...],
            mapping: dict[str, PlayerEvent],
    ) -> QChartView:
        set0, set1, categories = [], [], []
        for metric in metrics:
            value0, value1 = metric.get_components_values(mapping)
            set0.append(value0)
            set1.append(value1)
            categories.append(metric.name)
        builder = StackedBarChartBuilder()
        return builder.build(title, (set0, set1), set_names, categories)

    def faction_won_lost(self, mapping: dict[str, PlayerEvent]) -> QChartView:
        return self.bar_chart(
            "Wins/Losses per faction",
            ("Wins", "Losses"),
            FACTION_PLAYS_METRICS,
            mapping,
        )

    def tech_built_lost(self, mapping: dict[str, PlayerEvent]) -> QChartView:
        return self.bar_chart(
            "Survived/Lost",
            ("Survived", "Lost"),
            BUILT_LOST_METRICS,
            mapping,
        )

    def exp_built_lost(self, mapping: dict[str, PlayerEvent]) -> QChartView:
        return self.bar_chart(
            "Survived/Lost experimentals",
            ("Survived", "Lost"),
            EXPERIMENTALS_BUILT_LOST_METRICS,
            mapping,
        )

    def game_types_played(self, ratings: list[LeaderboardRating]) -> QChartView:
        pie_data = [
            (rating.leaderboard.pretty_name, rating.total_games)
            for rating in ratings
        ]
        builder = PieChartBuilder()
        return builder.build("Games played", pie_data)

    def player_events_charts(self, events: list[PlayerEvent]) -> Generator[QChartView, None, None]:
        mapping = {player_event.event.xd: player_event for player_event in events}
        yield self.faction_won_lost(mapping)
        yield self.tech_built_lost(mapping)
        yield self.exp_built_lost(mapping)
