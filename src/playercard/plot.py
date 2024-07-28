from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

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
        if len(self.series.x()) == 0:
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


class LineSeries:
    def __init__(self, size: int = 0) -> None:
        self._x: np.ndarray = np.zeros(size)
        self._y: np.ndarray = np.zeros(size)

    def x(self) -> np.ndarray:
        return self._x

    def y(self) -> np.ndarray:
        return self._y

    def set_point(self, index: int, point: QPointF) -> None:
        self._x[index] = point.x()
        self._y[index] = point.y()

    def extend(self, series: LineSeries) -> None:
        self._x = np.append(self._x, series.x())
        self._y = np.append(self._y, series.y())

    def point_at(self, index: int) -> QPointF:
        return QPointF(self._x[index], self._y[index])


class PlotController:
    def __init__(self, widget: pg.PlotWidget) -> None:
        self.widget = widget
        self.widget.setBackground("#202025")
        self.widget.setAxisItems({"bottom": DateAxisItem()})
        self.series = LineSeries()
        self.crosshairs = Crosshairs(self.widget, self.series)
        self.hide_irrelevant_plot_actions()
        self.add_custom_menu_actions()

    def clear(self) -> None:
        self.widget.clear()

    def draw_series(self) -> None:
        self.widget.plot(self.series.x(), self.series.y(), pen=pg.mkPen("orange"))
        self.widget.autoRange()

    def add_data(self, series: LineSeries) -> None:
        self.series.extend(series)

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
