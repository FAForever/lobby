from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QListView

from contextmenu.playercontextmenu import PlayerContextMenu
from replays.scoreboarditemdelegate import ScoreboardModelItem


class ScoreboardListView(QListView):
    def __init__(self) -> None:
        QListView.__init__(self)
        self.menu_handler = None

    def set_menu_handler(self, menu_handler: PlayerContextMenu) -> None:
        self.menu_handler = menu_handler

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QListView.mousePressEvent(self, event)
        if event.button() == Qt.MouseButton.RightButton:
            row = self.indexAt(event.pos()).row()
            if row != -1:
                index = self.model().index(row, 0)
                self.context_menu(index.data())

    def context_menu(self, item: ScoreboardModelItem) -> None:
        if self.menu_handler is None:
            return
        menu = self.menu_handler.get_context_menu(item.login(), int(item.player.xd))
        menu.popup(QCursor.pos())
