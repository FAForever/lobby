from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

import util
from config import Settings

FormClass, BaseClass = util.THEME.loadUiType("unitdb/unitdb.ui")


class UnitDbView(FormClass, BaseClass):
    def __init__(self) -> None:
        super(BaseClass, self).__init__()
        self.setupUi(self)


class UnitDBTab:
    def __init__(self) -> None:
        self.db_widget = UnitDbView()
        self._db_url = QUrl(Settings.get("UNITDB_URL"))
        self._db_url_alt = QUrl(Settings.get("UNITDB_SPOOKY_URL"))

        self.db_widget.fafDbButton.pressed.connect(self.open_default_tab)
        self.db_widget.spookyDbButton.pressed.connect(self.open_alternative_tab)

    def open_default_tab(self) -> None:
        QDesktopServices.openUrl(self._db_url)

    def open_alternative_tab(self) -> None:
        QDesktopServices.openUrl(self._db_url_alt)
