from PyQt6 import QtWidgets
from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import QRect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QHoverEvent
from PyQt6.QtGui import QPainter


class VerticalHeaderView(QtWidgets.QHeaderView):
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
        opt = QtWidgets.QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = index

        data = self.model().headerData(index, self.orientation(), Qt.ItemDataRole.DisplayRole)
        opt.text = str(data)

        opt.textAlignment = Qt.AlignmentFlag.AlignCenter

        state = QtWidgets.QStyle.StateFlag.State_None

        if self.highlightSections():
            if self.selectionModel().rowIntersectsSelection(index, QModelIndex()):
                state |= QtWidgets.QStyle.StateFlag.State_On
            elif index == self.hover:
                state |= QtWidgets.QStyle.StateFlag.State_MouseOver

        opt.state |= state

        self.style().drawControl(QtWidgets.QStyle.ControlElement.CE_Header, opt, painter, self)

    def mouseMoveEvent(self, event):
        QtWidgets.QHeaderView.mouseMoveEvent(self, event)
        self.parent().updateHoverRow(event)
        self.updateHoverSection(event)

    def wheelEvent(self, event):
        QtWidgets.QHeaderView.wheelEvent(self, event)
        self.parent().updateHoverRow(event)
        self.updateHoverSection(event)

    def mousePressEvent(self, event):
        QtWidgets.QHeaderView.mousePressEvent(self, event)
        self.parent().updateHoverRow(event)
        self.updateHoverSection(event)

    def updateHoverSection(self, event: QHoverEvent) -> None:
        index = self.logicalIndexAt(event.position().toPoint())
        oldHover = self.hover
        self.hover = index

        if self.hover != oldHover:
            if oldHover != -1:
                self.updateSection(oldHover)
            if self.hover != -1:
                self.updateSection(self.hover)
