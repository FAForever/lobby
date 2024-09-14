from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import QRect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyleOptionViewItem

from src.qt.itemviews.tableitemdelegte import TableItemDelegate
from src.qt.utils import qpainter


class LeaderboardItemDelegate(TableItemDelegate):
    def paint(
            self,
            painter: QPainter,
            option: QStyleOptionViewItem,
            index: QModelIndex,
    ) -> None:
        opt = self._customize_style_option(option, index)
        text = opt.text

        with qpainter(painter):
            self._draw_clear_option(painter, opt)
            self._set_pen(painter, opt)
            if index.column() == 0:
                rect = QRect(opt.rect)
                rect.setLeft(int(opt.rect.left() + opt.rect.width() // 2.125))
                alignment_flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                painter.drawText(rect, alignment_flags, text)
            else:
                painter.drawText(opt.rect, Qt.AlignmentFlag.AlignCenter, text)
