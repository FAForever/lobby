
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from src import util
from src.vaults.modvault import utils

FormClass, BaseClass = util.THEME.loadUiType("vaults/modvault/uimod.ui")


class UIModWidget(FormClass, BaseClass):
    FORMATTER_UIMOD = str(util.THEME.readfile("vaults/modvault/uimod.qthtml"))

    def __init__(self, parent, *args, **kwargs):
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)
        self.parent = parent

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        self.setWindowTitle("Ui Mod Manager")

        self.doneButton.clicked.connect(self.doneClicked)
        self.modList.itemEntered.connect(self.hoverOver)
        allmods = utils.getInstalledMods()
        self.uimods = {}
        for mod in allmods:
            if mod.ui_only:
                self.uimods[mod.totalname] = mod
                self.modList.addItem(mod.totalname)

        names = [mod.totalname for mod in utils.getActiveMods(uimods=True)]
        for name in names:
            activeModList = self.modList.findItems(
                name, QtCore.Qt.MatchFlag.MatchExactly,
            )
            if activeModList:
                activeModList[0].setSelected(True)

        if len(self.uimods) != 0:
            self.hoverOver(self.modList.item(0))

    def load_stylesheet(self):
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    @QtCore.pyqtSlot()
    def doneClicked(self):
        selected_mods = [
            self.uimods[str(item.text())]
            for item in self.modList.selectedItems()
        ]
        succes = utils.setActiveMods(selected_mods, False)
        if not succes:
            QtWidgets.QMessageBox.information(
                None,
                "Error",
                (
                    "Could not set the active UI mods. Maybe something is "
                    "wrong with your game.prefs file. Please send your log."
                ),
            )
        self.done(1)

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def hoverOver(self, item):
        mod = self.uimods[str(item.text())]
        self.modInfo.setText(
            self.FORMATTER_UIMOD.format(
                name=mod.totalname,
                description=mod.description,
            ),
        )
