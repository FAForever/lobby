from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyleOptionViewItem

from qt.itemviews.tableitemdelegte import TableItemDelegate
from util.qt import qpainter


class CoopLeaderboardItemDelegate(TableItemDelegate):
    def _customize_style_option(
            self,
            option: QStyleOptionViewItem,
            index: QModelIndex,
    ) -> QStyleOptionViewItem:
        opt = TableItemDelegate._customize_style_option(self, option, index)
        if option.styleObject.hover_index() == index:
            opt.state |= QStyle.StateFlag.State_HasFocus
        return opt

    def paint(
            self,
            painter: QPainter,
            option: QStyleOptionViewItem,
            index: QModelIndex,
    ) -> None:
        opt = self._customize_style_option(option, index)
        text = opt.text

        replay_col = 4

        with qpainter(painter):
            self._draw_clear_option(painter, opt)
            if index.column() == replay_col and opt.state & QStyle.StateFlag.State_HasFocus:
                font = opt.font
                font.setUnderline(True)
                painter.setFont(font)
                painter.setPen(opt.palette.link().color())
            else:
                self._set_pen(painter, opt)
            painter.drawText(opt.rect, Qt.AlignmentFlag.AlignCenter, text)
