from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtGui import QMouseEvent

from src.qt.itemviews.tableview import TableView


class LeaderboardTableView(TableView):
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            row = self.indexAt(event.pos()).row()
            if row != -1:
                name_index = self.model().index(row, 0)
                id_index = self.model().index(row, 8)
                name = self.model().data(name_index)
                uid = int(self.model().data(id_index))
                self.selectRow(row)
                self.context_menu(name, uid)
            self.update_hover_row(event)
            self.verticalHeader().update_hover_section(event)
        else:
            TableView.mousePressEvent(self, event)

    def context_menu(self, name: str, uid: int) -> None:
        client = self.parent().parent().client
        menu = client.player_ctx_menu.get_context_menu(name, uid)
        menu.popup(QCursor.pos())
