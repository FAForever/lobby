from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import QRect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QHoverEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyleOptionHeader


class VerticalHeaderView(QHeaderView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(Qt.Orientation.Vertical, *args, **kwargs)
        self.setHighlightSections(True)
        self.setSectionResizeMode(self.ResizeMode.Fixed)
        self.setVisible(True)
        self.setSectionsClickable(True)
        self.setAlternatingRowColors(True)
        self.setObjectName("VerticalHeader")

        self.hover = -1

    def paintSection(self, painter: QPainter, rect: QRect, index: QModelIndex) -> None:
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = index

        data = self.model().headerData(index, self.orientation(), Qt.ItemDataRole.DisplayRole)
        opt.text = str(data)

        opt.textAlignment = Qt.AlignmentFlag.AlignCenter

        state = QStyle.StateFlag.State_None

        if self.highlightSections():
            if self.selectionModel().rowIntersectsSelection(index, QModelIndex()):
                state |= QStyle.StateFlag.State_On
            elif index == self.hover:
                state |= QStyle.StateFlag.State_MouseOver

        opt.state |= state

        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        QHeaderView.mouseMoveEvent(self, event)
        self.parent().update_hover_row(event)
        self.update_hover_section(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        QHeaderView.wheelEvent(self, event)
        self.parent().update_hover_row(event)
        self.update_hover_section(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QHeaderView.mousePressEvent(self, event)
        self.parent().update_hover_row(event)
        self.update_hover_section(event)

    def update_hover_section(self, event: QHoverEvent) -> None:
        index = self.logicalIndexAt(event.position().toPoint())
        old_hover, self.hover = self.hover, index

        if self.hover != old_hover:
            if old_hover != -1:
                self.updateSection(old_hover)
            if self.hover != -1:
                self.updateSection(self.hover)
