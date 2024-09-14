from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QStyleFactory

from src import util
from src.config import Settings

FormClass, BaseClass = util.THEME.loadUiType("client/change_style.ui")


class ChangeAppStyleDialog(FormClass, BaseClass):
    def __init__(self) -> None:
        super(ChangeAppStyleDialog, self).__init__()
        self.setupUi(self)
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))
        self.setWindowTitle("Select Application Style")
        self.stylesList.addItems(QStyleFactory.keys())
        self.buttonBox.clicked.connect(self.on_button_clicked)

    def highlight_current_style(self) -> None:
        current_stylename = QApplication.style().name()
        match_flag = QtCore.Qt.MatchFlag.MatchFixedString
        current_item, = self.stylesList.findItems(current_stylename, match_flag)
        self.stylesList.setCurrentItem(current_item)

    def run(self) -> int:
        self.highlight_current_style()
        return self.exec()

    def on_button_clicked(self, button: QPushButton) -> None:
        roles = self.buttonBox.ButtonRole
        role = self.buttonBox.buttonRole(button)
        style_name = self.stylesList.currentItem().text()
        if role == roles.ApplyRole:
            self.select_style(style_name, apply=True)
        elif role == roles.AcceptRole:
            self.select_style(style_name, apply=False)

    def save_preference(self, stylename: str) -> None:
        Settings.set("theme/style", stylename)

    def select_style(self, stylename: str, apply: bool) -> None:
        self.save_preference(stylename)
        if apply:
            QApplication.setStyle(QStyleFactory.create(stylename))


class ThemeMenu(QtCore.QObject):
    themeSelected = QtCore.pyqtSignal(object)

    def __init__(self, menu):
        QtCore.QObject.__init__(self)
        self._menu = menu
        self._themes = {}
        # Hack to not process check signals when we're changing them ourselves
        self._updating = False
        self.app_style_handler = ChangeAppStyleDialog()

    def setup(self, themes):
        for theme in themes:
            action = self._menu.addAction(str(theme))
            action.toggled.connect(self.handle_toggle)
            self._themes[action] = theme
            action.setCheckable(True)
        self._menu.addSeparator()
        self._menu.addAction("Reload Stylesheet", util.THEME.reloadStyleSheets)
        self._menu.addSeparator()
        self._menu.addAction("Change Style", self.app_style_handler.run)

        self._updateThemeChecks()

    def _updateThemeChecks(self):
        self._updating = True
        new_theme = util.THEME.theme.name
        for action in self._themes:
            action.setChecked(new_theme == self._themes[action])
        self._updating = False

    def handle_toggle(self, toggled):
        if self._updating:
            return

        action = self.sender()
        if not toggled:
            self._updating = True
            action.setChecked(True)
            self._updating = False
        else:
            self.themeSelected.emit(self._themes[action])
            self._updateThemeChecks()
