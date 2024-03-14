from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPainter


class LeaderboardItemDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
            self,
            painter: QPainter,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex,
    ) -> None:
        opt = QtWidgets.QStyleOptionViewItem(option)
        opt.state &= ~QtWidgets.QStyle.StateFlag.State_HasFocus
        opt.state &= ~QtWidgets.QStyle.StateFlag.State_MouseOver

        view = opt.styleObject
        behavior = view.selectionBehavior()
        hoverIndex = view.hoverIndex()

        if (
            not (option.state & QtWidgets.QStyle.StateFlag.State_Selected)
            and behavior is not QtWidgets.QTableView.SelectionBehavior.SelectItems
        ):
            if (
                behavior is QtWidgets.QTableView.SelectionBehavior.SelectRows
                and hoverIndex.row() == index.row()
            ):
                opt.state |= QtWidgets.QStyle.StateFlag.State_MouseOver

        self.initStyleOption(opt, index)
        painter.save()
        text = opt.text
        opt.text = ""
        control_element = QtWidgets.QStyle.ControlElement.CE_ItemViewItem
        opt.widget.style().drawControl(control_element, opt, painter, opt.widget)
        if opt.state & QtWidgets.QStyle.StateFlag.State_Selected:
            painter.setPen(QtCore.Qt.GlobalColor.white)
        if index.column() == 0:
            rect = QtCore.QRect(opt.rect)
            rect.setLeft(int(opt.rect.left() + opt.rect.width() // 2.125))
            alignment_flags = (
                QtCore.Qt.AlignmentFlag.AlignLeft
                | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            painter.drawText(rect, alignment_flags, text)
        else:
            painter.drawText(opt.rect, QtCore.Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
