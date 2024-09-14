from __future__ import annotations

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from src import config
from src import util
from src.games.mapgenoptions import ComboBoxOption
from src.games.mapgenoptions import RangeOption
from src.games.mapgenoptions import SpinBoxOption
from src.games.mapgenoptionsvalues import GenerationType
from src.games.mapgenoptionsvalues import MapStyle
from src.games.mapgenoptionsvalues import PropStyle
from src.games.mapgenoptionsvalues import ResourceStyle
from src.games.mapgenoptionsvalues import Sentinel
from src.games.mapgenoptionsvalues import TerrainStyle
from src.games.mapgenoptionsvalues import TerrainSymmetry
from src.games.mapgenoptionsvalues import TextureStyle
from src.mapGenerator.mapgenManager import MapGeneratorManager

FormClass, BaseClass = util.THEME.loadUiType("games/mapgen.ui")


class MapGenDialog(FormClass, BaseClass):
    map_generated = QtCore.pyqtSignal(str)

    def __init__(self, mapgen_manager: MapGeneratorManager, *args, **kwargs) -> None:
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)

        self.load_stylesheet()

        self.mapgen_manager = mapgen_manager

        self.mapNamePlainTextEdit.textChanged.connect(self.user_mapname_changed)
        self.useCustomStyleCheckBox.checkStateChanged.connect(self.on_custom_style)
        self.generationType.currentTextChanged.connect(self.gen_type_changed)
        self.mapSize.valueChanged.connect(self.map_size_changed)
        self.propGenerator.currentTextChanged.connect(self.prop_generator_changed)
        self.resourceGenerator.currentTextChanged.connect(self.resource_generator_changed)
        self.generateMapButton.clicked.connect(self.generate_map)
        self.saveMapGenSettingsButton.clicked.connect(self.save_preferences_and_quit)
        self.resetMapGenSettingsButton.clicked.connect(self.reset_mapgen_prefs)

        self.cmd_options: list[ComboBoxOption | SpinBoxOption | RangeOption] = [
            ComboBoxOption(
                "visibility",
                self.generationType,
                GenerationType.CASUAL.value,
                GenerationType.values(),
            ),
            ComboBoxOption(
                "terrain-symmetry",
                self.terrainSymmetry,
                Sentinel.RANDOM.value,
                Sentinel.values() + TerrainSymmetry.values(),
            ),
            ComboBoxOption(
                "style",
                self.mapStyle,
                Sentinel.RANDOM.value,
                Sentinel.values() + MapStyle.values(),
            ),
            ComboBoxOption(
                "terrain-style",
                self.terrainStyle,
                Sentinel.RANDOM.value,
                Sentinel.values() + TerrainStyle.values(),
            ),
            ComboBoxOption(
                "texture-style",
                self.textureStyle,
                Sentinel.RANDOM.value,
                Sentinel.values() + TextureStyle.values(),
            ),
            ComboBoxOption(
                "resource-style",
                self.resourceGenerator,
                Sentinel.RANDOM.value,
                Sentinel.values() + ResourceStyle.values(),
            ),
            ComboBoxOption(
                "prop-style",
                self.propGenerator,
                Sentinel.RANDOM.value,
                Sentinel.values() + PropStyle.values(),
            ),
            SpinBoxOption("spawn-count", self.numberOfSpawns, int, 2),
            SpinBoxOption("num-teams", self.numberOfTeams, int, 2),
            SpinBoxOption("map-size", self.mapSize, float, 5),
            RangeOption(
                "resource-density",
                SpinBoxOption("", self.minResourceDensity, int, 0),
                SpinBoxOption("", self.maxResourceDensity, int, 100),
            ),
            RangeOption(
                "reclaim-density",
                SpinBoxOption("", self.minReclaimDensity, int, 0),
                SpinBoxOption("", self.maxReclaimDensity, int, 100),
            ),
        ]
        self.load_preferences()

    @QtCore.pyqtSlot()
    def user_mapname_changed(self) -> None:
        mapname = self.mapNamePlainTextEdit.toPlainText()
        self.optionsFrame.setEnabled(mapname.strip() == "")

    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def on_custom_style(self, state: QtCore.Qt.CheckState) -> None:
        self.customStyleGroupBox.setEnabled(state == QtCore.Qt.CheckState.Checked)
        self.mapStyle.setEnabled(state == QtCore.Qt.CheckState.Unchecked)

    def load_stylesheet(self):
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def keyPressEvent(self, event):
        if (
            event.key() == QtCore.Qt.Key.Key_Enter
            or event.key() == QtCore.Qt.Key.Key_Return
        ):
            return
        QtWidgets.QDialog.keyPressEvent(self, event)

    @staticmethod
    def nearest_to_multiple(value: float, to: float) -> float:
        return ((value + to / 2) // to) * to

    @QtCore.pyqtSlot(float)
    def map_size_changed(self, value):
        if (value % 1.25) == 0:
            return
        value = self.nearest_to_multiple(value, 1.25)
        self.mapSize.blockSignals(True)
        self.mapSize.setValue(value)
        self.mapSize.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def gen_type_changed(self, text: str) -> None:
        self.casualOptionsFrame.setEnabled(text == GenerationType.CASUAL.value)

    @QtCore.pyqtSlot(str)
    def resource_generator_changed(self, text: str) -> None:
        self.minResourceDensity.setEnabled(text != Sentinel.RANDOM.value)
        self.maxResourceDensity.setEnabled(text != Sentinel.RANDOM.value)

    @QtCore.pyqtSlot(str)
    def prop_generator_changed(self, text: str) -> None:
        self.minReclaimDensity.setEnabled(text != Sentinel.RANDOM.value)
        self.maxReclaimDensity.setEnabled(text != Sentinel.RANDOM.value)

    @QtCore.pyqtSlot()
    def load_preferences(self) -> None:
        for option in self.cmd_options:
            option.load()
        self.useCustomStyleCheckBox.setChecked(
            config.Settings.get(
                "mapGenerator/useCustomStyle",
                type=bool,
                default=False,
            ),
        )
        self.on_custom_style(self.useCustomStyleCheckBox.checkState())

    def save_preferences(self) -> None:
        for option in self.cmd_options:
            option.save()
        config.Settings.set(
            "mapGenerator/useCustomStyle",
            self.useCustomStyleCheckBox.isChecked(),
        )

    @QtCore.pyqtSlot()
    def save_preferences_and_quit(self) -> None:
        self.save_preferences()
        self.done(1)

    @QtCore.pyqtSlot()
    def reset_mapgen_prefs(self) -> None:
        for option in self.cmd_options:
            option.reset()

    @QtCore.pyqtSlot()
    def generate_map(self) -> None:
        if result := self.mapgen_manager.generateMap(args=self.set_arguments()):
            self.map_generated.emit(result)
            self.save_preferences_and_quit()
        else:
            self.save_preferences()

    def set_arguments(self) -> list[str]:
        args = []
        if mapname := self.mapNamePlainTextEdit.toPlainText().strip():
            args.extend(["--map-name", mapname])
        else:
            for option in self.cmd_options:
                if option.name == "map-size":
                    args.append("--map-size")
                    size_px = int(option.value() * 51.2)
                    args.append(str(size_px))
                elif option.active():
                    args.extend(option.as_cmd_arg())
        return args
