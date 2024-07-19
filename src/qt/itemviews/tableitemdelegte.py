from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyleOptionViewItem
from PyQt6.QtWidgets import QTableView

from util.qt import qpainter
from util.qtstyleditemdelegate import QtStyledItemDelegate


class TableItemDelegate(QtStyledItemDelegate):
    """
    Highlights the entire row on mouse hover when table's
    SelectionBehavior is set to SelectRows
    Requires TableView to have method hover_index() defined
    """

    def _customize_style_option(
            self,
            option: QStyleOptionViewItem,
            index: QModelIndex,
    ) -> QStyleOptionViewItem:
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.state &= ~QStyle.StateFlag.State_MouseOver

        view = opt.styleObject
        behavior = view.selectionBehavior()
        hover_index = view.hover_index()

        if (
            not (option.state & QStyle.StateFlag.State_Selected)
            and behavior != QTableView.SelectionBehavior.SelectItems
        ):
            if (
                behavior == QTableView.SelectionBehavior.SelectRows
                and hover_index.row() == index.row()
            ):
                opt.state |= QStyle.StateFlag.State_MouseOver

        self.initStyleOption(opt, index)
        return opt

    def _set_pen(self, painter: QPainter, option: QStyleOptionViewItem) -> None:
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(Qt.GlobalColor.white)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        opt = self._customize_style_option(option, index)
        text = opt.text

        with qpainter(painter):
            self._draw_clear_option(painter, opt)
            self._set_pen(painter, opt)
            painter.drawText(opt.rect, Qt.AlignmentFlag.AlignCenter, text)
