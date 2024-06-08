from PyQt6.QtCore import QAbstractTableModel
from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QUrl

from api.models.CoopResult import CoopResult


class CoopLeaderBoardModel(QAbstractTableModel):
    def __init__(self, data: dict[str, list[CoopResult]]) -> None:
        QAbstractTableModel.__init__(self)
        self._headers = ("Players", "Names", "Duration", "Secondary Objectives", "Replay")
        self.load_data(data)

    def load_data(self, data: dict[str, list[CoopResult]]) -> None:
        self.values = data["values"]
        self.column_count = len(self._headers)
        self.row_count = len(self.values)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self.row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self.column_count

    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: Qt.ItemDataRole,
    ) -> str | Qt.AlignmentFlag | None:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section + 1)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

    def data(
            self,
            index: QModelIndex,
            role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole,
    ) -> str | QUrl | None:
        column = index.column()
        row = index.row()

        if role == Qt.ItemDataRole.DisplayRole:
            coopres = self.values[row]
            if column == 0:
                return str(coopres.player_count)
            elif column == 1:
                return ", ".join([stats.player.login for stats in coopres.game.player_stats])
            elif column == 2:
                mm, ss = divmod(coopres.duration, 60)
                hh, mm = divmod(mm, 60)
                return f"{hh:02}:{mm:02}:{ss:02}"
            elif column == 3:
                return "Yes" if coopres.secondary_objectives else "No"
            elif column == 4:
                return "Watch"
        if role == Qt.ItemDataRole.UserRole and column == 4:
            coopres = self.values[row]
            return QUrl(coopres.game.replay_url)
