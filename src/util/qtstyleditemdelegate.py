from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtWidgets import QStyleOptionViewItem


class QtStyledItemDelegate(QStyledItemDelegate):
    def _get_elided_text(
            self,
            painter: QPainter,
            text: str,
            mode: Qt.TextElideMode = Qt.TextElideMode.ElideRight,
            width: int = 0,
    ) -> str:
        metrics = painter.fontMetrics()
        return metrics.elidedText(text, mode, width)

    def _draw_clear_option(self, painter: QPainter, option: QStyleOptionViewItem) -> None:
        option.icon = QIcon()
        option.text = ""
        control_element = QStyle.ControlElement.CE_ItemViewItem
        option.widget.style().drawControl(control_element, option, painter, option.widget)
