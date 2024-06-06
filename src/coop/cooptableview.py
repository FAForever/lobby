from PyQt6.QtCore import Qt
from PyQt6.QtCore import QUrl
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent

from qt.itemviews.tableview import TableView


class CoopLeaderboardTableView(TableView):
    url_clicked = pyqtSignal(QUrl)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self.indexAt(event.position().toPoint())
        if index.column() == 4:
            url = self.model().data(index, Qt.ItemDataRole.UserRole)
            self.url_clicked.emit(url)
            return

        return TableView.mousePressEvent(self, event)
