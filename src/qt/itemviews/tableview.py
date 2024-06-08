from PyQt6.QtCore import QModelIndex
from PyQt6.QtGui import QHoverEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QTableView

from qt.itemviews.tableheaderview import VerticalHeaderView


class TableView(QTableView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
        self.setSelectionMode(self.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        self.setVerticalHeader(VerticalHeaderView())
        self.m_hover_row = -1
        self.m_hover_column = -1

    def hover_index(self) -> QModelIndex:
        return QModelIndex(self.model().index(self.m_hover_row, self.m_hover_column))

    def update_hover_row(self, event: QHoverEvent) -> None:
        index = self.indexAt(event.position().toPoint())
        old_hover_row = self.m_hover_row
        self.m_hover_row = index.row()
        self.m_hover_column = index.column()

        if (
            self.selectionBehavior() is self.SelectionBehavior.SelectRows
            and old_hover_row != self.m_hover_row
        ):
            if old_hover_row != -1:
                for i in range(self.model().columnCount()):
                    self.update(self.model().index(old_hover_row, i))
            if self.m_hover_row != -1:
                for i in range(self.model().columnCount()):
                    self.update(self.model().index(self.m_hover_row, i))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        QTableView.mouseMoveEvent(self, event)
        self.update_hover_row(event)
        self.verticalHeader().update_hover_section(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        QTableView.wheelEvent(self, event)
        self.update_hover_row(event)
        self.verticalHeader().update_hover_section(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QTableView.mousePressEvent(self, event)
        self.update_hover_row(event)
        self.verticalHeader().update_hover_section(event)
