from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QTableWidgetItem

from src import util
from src.config import Settings
from src.games.filters.filter import FILTER_OPERATIONS
from src.games.filters.filter import FILTER_OPTIONS
from src.games.filters.filter import GameFilter

ManagerForm, ManagerBase = util.THEME.loadUiType("games/filtermanager.ui")


class GameFilterManager(ManagerForm, ManagerBase):
    def __init__(self) -> None:
        ManagerBase.__init__(self)
        self.setupUi(self)
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

        self.addButton.clicked.connect(self.open_creator)
        self.removeButton.clicked.connect(self.remove_filter)
        self.filtersTableWidget.setColumnHidden(0, True)  # hide id column

        self.filters: list[GameFilter] = []
        self.load_filters()

    def load_filters(self) -> None:
        with Settings.group("fa.games.filters") as group:
            for uid in sorted(map(int, group.childKeys())):
                game_filter = GameFilter(uid, *map(str.strip, group.value(str(uid)).split(",", 2)))
                self.filters.append(game_filter)
                self.append_to_table(game_filter)

    def remove_filter(self) -> None:
        if len(self.filtersTableWidget.selectedItems()) == 0:
            return

        row = self.filtersTableWidget.currentRow()
        id_item = self.filtersTableWidget.item(row, 0)
        with Settings.group("fa.games.filters") as group:
            group.remove(id_item.text())
        self.filtersTableWidget.removeRow(row)
        self.filters.pop(row)

    def append_to_table(self, game_filter: GameFilter) -> None:
        rows = self.filtersTableWidget.rowCount()
        cols = self.filtersTableWidget.columnCount()
        self.filtersTableWidget.setRowCount(rows + 1)

        for col, content in zip(range(cols), game_filter):
            item = QTableWidgetItem(str(content))
            self.filtersTableWidget.setItem(rows, col, item)

    def open_creator(self) -> None:
        last_uid = max(self.filters).uid if len(self.filters) > 0 else 0
        creator = FilterCreator(last_uid + 1)
        creator.exec()
        if creator.result() == self.DialogCode.Accepted.value:
            self.save(creator.result_filter())

    def save(self, game_filter: GameFilter | None) -> None:
        if game_filter is None:
            return

        with Settings.group("fa.games.filters") as group:
            group.setValue(str(game_filter.uid), game_filter.serialize())

        self.filters.append(game_filter)
        self.append_to_table(game_filter)


CreatorForm, CreatorBase = util.THEME.loadUiType("games/filtercreator.ui")


class FilterCreator(CreatorForm, CreatorBase):
    def __init__(self, filter_id: int) -> None:
        CreatorBase.__init__(self)
        self.setupUi(self)
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

        self.filterTypeComboBox.addItems(FILTER_OPTIONS)
        self.constraintComboBox.addItems(FILTER_OPERATIONS)

        self.filters: list[GameFilterManager] = []
        self.accepted.connect(self.on_accept)
        self.filter_id = filter_id
        self._result_filter: GameFilter | None = None

    def on_accept(self) -> None:
        text = self.lineEdit.text()
        if text != "":
            game_filter = GameFilter(
                self.filter_id,
                self.filterTypeComboBox.currentText(),
                self.constraintComboBox.currentText(),
                text,
            )
            self._result_filter = game_filter

    def result_filter(self) -> GameFilter | None:
        return self._result_filter

    def showEvent(self, event: QShowEvent) -> None:
        CreatorBase.showEvent(self, event)
        self.lineEdit.setFocus(Qt.FocusReason.MouseFocusReason)
