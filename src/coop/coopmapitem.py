from __future__ import annotations

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

import util
from api.models.CoopMission import CoopMission


class CoopMapItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, *args, **kwargs) -> None:
        QtWidgets.QStyledItemDelegate.__init__(self, *args, **kwargs)

    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        textOption = QtGui.QTextOption()
        textOption.setWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        html.setDefaultTextOption(textOption)

        html.setTextWidth(option.rect.width())
        html.setHtml(option.text)

        # clear text before letting the control draw itself because we're
        # rendering these parts ourselves
        option.text = ""
        option.widget.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget,
        )
        # Description
        painter.translate(option.rect.left(), option.rect.top())
        clip = QtCore.QRectF(0, 0, option.rect.width(), option.rect.height())
        html.drawContents(painter, clip)

        painter.restore()

    def sizeHint(
            self,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex,
            *args,
            **kwargs,
    ) -> None:
        self.initStyleOption(option, index)
        html = QtGui.QTextDocument()
        textOption = QtGui.QTextOption()
        textOption.setWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        html.setTextWidth(option.rect.width())
        html.setDefaultTextOption(textOption)
        html.setHtml(option.text)

        return QtCore.QSize(
            int(html.size().width()) + 10,
            int(html.size().height()) + 10,
        )


class CoopMapItem(QtWidgets.QTreeWidgetItem):

    FORMATTER_COOP = str(util.THEME.readfile("coop/formatters/coop.qthtml"))

    def __init__(self, order: int, parent: QtWidgets.QWidget, *args, **kwargs) -> None:
        QtWidgets.QTreeWidgetItem.__init__(self, *args, **kwargs)

        self.order = order
        self.parent = parent

        self.name = None
        self.description = None
        self.mapname = None
        self.options = []

        self.setHidden(True)

    def update(self, mission: CoopMission) -> None:
        """
        Updates this item from the message dictionary supplied
        """

        self.name = mission.name
        self.mapname = mission.folder_name
        self.description = mission.description
        self.mission = mission

        self.viewtext = self.FORMATTER_COOP.format(
            name=self.name,
            description=self.description,
        )

        # adding tag is just a silly trick to make text rich and force
        # QToolTip to enable word wrap
        self.setToolTip(0, f"<qt>{self.description}</qt>")

    def display(self, column):
        if column == 0:
            return self.viewtext
        if column == 1:
            return self.viewtext

    def data(self, column, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.display(column)
        elif role == QtCore.Qt.ItemDataRole.UserRole:
            return self
        return super(CoopMapItem, self).data(column, role)

    def __ge__(self, other):
        """ Comparison operator used for item list sorting """
        return not self.__lt__(other)

    def __lt__(self, other: CoopMapItem) -> bool:
        """ Comparison operator used for item list sorting """
        # Default: order
        return self.order > other.order
