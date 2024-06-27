from __future__ import annotations

import random
from enum import Enum
from typing import NamedTuple

from PyQt6 import QtCore
from PyQt6 import QtWidgets

import config
import util

FormClass, BaseClass = util.THEME.loadUiType("games/mapgen.ui")


class Common(Enum):
    RANDOM = "RANDOM"


class Density(NamedTuple):
    minval: int
    maxval: int

    def value(self) -> float:
        return random.randrange(self.minval, self.maxval + 1) / 100


class GenerationType(Enum):
    CASUAL = "CASUAL"
    TOURNAMENT = "TOURNAMENT"
    BLIND = "BLIND"
    UNEXPLORED = "UNEXPLORED"


class TerrainSymmtery(Enum):
    RANDOM = "RANDOM"

    POINT2 = "POINT2"
    POINT3 = "POINT3"
    POINT4 = "POINT4"
    POINT5 = "POINT5"
    POINT6 = "POINT6"
    POINT7 = "POINT7"
    POINT8 = "POINT8"
    POINT9 = "POINT9"
    POINT10 = "POINT10"
    POINT11 = "POINT11"
    POINT12 = "POINT12"
    POINT13 = "POINT13"
    POINT14 = "POINT14"
    POINT15 = "POINT15"
    POINT16 = "POINT16"
    XZ = "XZ"
    ZX = "ZX"
    X = "X"
    Z = "Z"
    QUAD = "QUAD"
    DIAG = "DIAG"
    NONE = "NONE"


class MapStyle(Enum):
    RANDOM = "RANDOM"

    BASIC = "BASIC"
    BIG_ISLANDS = "BIG_ISLANDS"
    CENTER_LAKE = "CENTER_LAKE"
    DROP_PLATEAU = "DROP_PLATEAU"
    FLOODED = "FLOODED"
    HIGH_RECLAIM = "HIGH_RECLAIM"
    LAND_BRIDGE = "LAND_BRIDGE"
    LITTLE_MOUNTAIN = "LITTLE_MOUNTAIN"
    LOW_MEX = "LOW_MEX"
    MOUNTAIN_RANGE = "MOUNTAIN_RANGE"
    ONE_ISLAND = "ONE_ISLAND"
    SMALL_ISLANDS = "SMALL_ISLANDS"
    VALLEY = "VALLEY"

    @staticmethod
    def get_by_index(index: int) -> MapStyle:
        return list(MapStyle)[index]


class TerrainStyle(Enum):
    RANDOM = "RANDOM"

    BASIC = "BASIC"
    BIG_ISLANDS = "BIG_ISLANDS"
    CENTER_LAKE = "CENTER_LAKE"
    DROP_PLATEAU = "DROP_PLATEAU"
    FLOODED = "FLOODED"
    LAND_BRIDGE = "LAND_BRIDGE"
    LITTLE_MOUNTAIN = "LITTLE_MOUNTAIN"
    MOUNTAIN_RANGE = "MOUNTAIN_RANGE"
    ONE_ISLAND = "ONE_ISLAND"
    SMALL_ISLANDS = "SMALL_ISLANDS"
    VALLEY = "VALLEY"


class PropStyle(Enum):
    RANDOM = "RANDOM"

    BASIC = "BASIC"
    BOULDER_FIELD = "BOULDER_FIELD"
    ENEMY_CIV = "ENEMY_CIV"
    HIGH_RECLAIM = "HIGH_RECLAIM"
    LARGE_BATTLE = "LARGE_BATTLE"
    NAVY_WRECKS = "NAVY_WRECKS"
    NEUTRAL_CIV = "NEUTRAL_CIV"
    ROCK_FIELD = "ROCK_FIELD"
    SMALL_BATTLE = "SMALL_BATTLE"


class ResourceStyle(Enum):
    RANDOM = "RANDOM"

    BASIC = "BASIC"
    LOW_MEX = "LOW_MEX"
    WATER_MEX = "WATER_MEX"


class TextureStyle(Enum):
    RANDOM = "RANDOM"

    BRIMSTONE = "BRIMSTONE"
    DESERT = "DESERT"
    EARLYAUTUMN = "EARLYAUTUMN"
    FRITHEN = "FRITHEN"
    MARS = "MARS"
    MOONLIGHT = "MOONLIGHT"
    PRAYER = "PRAYER"
    STONES = "STONES"
    SUNSET = "SUNSET"
    SYRTIS = "SYRTIS"
    WINDINGRIVER = "WINDINGRIVER"
    WONDER = "WONDER"


class MapGenDialog(FormClass, BaseClass):
    def __init__(self, parent, *args, **kwargs):
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)

        self.load_stylesheet()

        self.parent = parent

        self.useCustomStyleCheckBox.checkStateChanged.connect(self.on_custom_style)
        self.useCustomStyleCheckBox.setChecked(
            config.Settings.get("mapGenerator/useCustomStyle", type=bool, default=False),
        )

        self.generationType.currentIndexChanged.connect(self.gen_type_changed)
        self.numberOfSpawns.currentIndexChanged.connect(self.num_spawns_changed)
        self.mapSize.valueChanged.connect(self.map_size_changed)
        self.mapStyle.currentIndexChanged.connect(self.map_style_changed)
        self.generateMapButton.clicked.connect(self.generate_map)
        self.saveMapGenSettingsButton.clicked.connect(self.save_mapgen_prefs)
        self.resetMapGenSettingsButton.clicked.connect(self.reset_mapgen_prefs)

        self.spinners = [
            self.minResourceDensity,
            self.maxResourceDensity,
            self.minReclaimDensity,
            self.maxReclaimDensity,
        ]

        self.generation_type = GenerationType.CASUAL
        self.number_of_spawns = 2
        self.map_size = 256
        self.map_style = MapStyle.RANDOM
        self.populate_options()
        self.load_preferences()

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

    @QtCore.pyqtSlot(int)
    def num_spawns_changed(self, index: int) -> None:
        self.number_of_spawns = 2 * (index + 1)

    @staticmethod
    def nearest_to_multiple(value: float, to: float) -> float:
        return ((value + to / 2) // to) * to

    @QtCore.pyqtSlot(float)
    def map_size_changed(self, value):
        if (value % 1.25):
            value = self.nearest_to_multiple(value, 1.25)
            self.mapSize.blockSignals(True)
            self.mapSize.setValue(value)
            self.mapSize.blockSignals(False)
        self.map_size = int(value * 51.2)

    @QtCore.pyqtSlot(int)
    def gen_type_changed(self, index: int) -> None:
        if index == -1 or index == 0:
            self.generation_type = GenerationType.CASUAL
        elif index == 1:
            self.generation_type = GenerationType.TOURNAMENT
        elif index == 2:
            self.generation_type = GenerationType.BLIND
        elif index == 3:
            self.generation_type = GenerationType.UNEXPLORED

        if index == -1 or index == 0:
            self.casualOptionsFrame.setEnabled(True)
            self.mapStyle.setCurrentIndex(
                config.Settings.get(
                    "mapGenerator/mapStyleIndex", type=int, default=0,
                ),
            )
        else:
            self.casualOptionsFrame.setEnabled(False)

    @QtCore.pyqtSlot(int)
    def map_style_changed(self, index: int) -> None:
        if index == -1 or index == 0:
            self.map_style = MapStyle.RANDOM
        else:
            self.map_style = MapStyle.get_by_index(index)

        self.checkRandomButtons()

    @QtCore.pyqtSlot()
    def checkRandomButtons(self):
        self.customStyleGroupBox.setEnabled(self.useCustomStyleCheckBox.isChecked())

    def populate_options(self) -> None:
        controls = (
            self.terrainStyle,
            self.terrainSymmetry,
            self.mapStyle,
            self.textureStyle,
            self.resourceGenerator,
            self.propGenerator,
        )
        control_classes = (
            TerrainStyle,
            TerrainSymmtery,
            MapStyle,
            TextureStyle,
            ResourceStyle,
            PropStyle,
        )
        for control, control_cls in zip(controls, control_classes):
            for style in iter(control_cls):
                control.addItem(style.value, style)

    @QtCore.pyqtSlot()
    def load_preferences(self) -> None:
        self.generationType.setCurrentIndex(
            config.Settings.get(
                "mapGenerator/generationTypeIndex", type=int, default=0,
            ),
        )
        self.numberOfSpawns.setCurrentIndex(
            config.Settings.get(
                "mapGenerator/numberOfSpawnsIndex", type=int, default=0,
            ),
        )
        self.mapSize.setValue(
            config.Settings.get(
                "mapGenerator/mapSize", type=float, default=5.0,
            ),
        )
        self.mapStyle.setCurrentIndex(
            config.Settings.get(
                "mapGenerator/mapStyleIndex", type=int, default=0,
            ),
        )

        for spinner in self.spinners:
            spinner.setValue(
                config.Settings.get(
                    f"mapGenerator/{spinner.objectName()}",
                    type=int,
                    default=spinner.value(),
                ),
            )

        self.useCustomStyleCheckBox.setChecked(
            config.Settings.get(
                "mapGenerator/useCustomStyle",
                type=bool,
                default=False,
            ),
        )
        self.terrainStyle.setCurrentText(
            config.Settings.get(
                "mapGenerator/terrainStyle",
                default=Common.RANDOM.value,
            ),
        )
        self.textureStyle.setCurrentText(
            config.Settings.get(
                "mapGenerator/textureStyle",
                default=Common.RANDOM.value,
            ),
        )
        self.propGenerator.setCurrentText(
            config.Settings.get(
                "mapGenerator/propGenerator",
                default=Common.RANDOM.value,
            ),
        )
        self.resourceGenerator.setCurrentText(
            config.Settings.get(
                "mapGenerator/resourceGenerator",
                default=Common.RANDOM.value,
            ),
        )
        self.terrainSymmetry.setCurrentText(
            config.Settings.get(
                "mapGenerator/terrainSymmetry",
                default=Common.RANDOM.value,
            ),
        )
        for spinner in self.spinners:
            spinner.setValue(
                config.Settings.get(
                    f"mapGenerator/{spinner.objectName()}",
                    type=int,
                    default=spinner.value(),
                ),
            )

    @QtCore.pyqtSlot()
    def save_mapgen_prefs(self) -> None:
        config.Settings.set(
            "mapGenerator/generationTypeIndex",
            self.generationType.currentIndex(),
        )
        config.Settings.set(
            "mapGenerator/mapSize",
            self.mapSize.value(),
        )
        config.Settings.set(
            "mapGenerator/numberOfSpawnsIndex",
            self.numberOfSpawns.currentIndex(),
        )
        config.Settings.set(
            "mapGenerator/mapStyleIndex",
            self.mapStyle.currentIndex(),
        )
        config.Settings.set(
            "mapGenerator/useCustomStyle",
            self.useCustomStyleCheckBox.isChecked(),
        )

        config.Settings.set(
            "mapGenerator/terrainStyle",
            self.terrainStyle.currentText(),
        )
        config.Settings.set(
            "mapGenerator/textureStyle",
            self.textureStyle.currentText(),
        )
        config.Settings.set(
            "mapGenerator/propGenerator",
            self.propGenerator.currentText(),
        )
        config.Settings.set(
            "mapGenerator/resourceGenerator",
            self.resourceGenerator.currentText(),
        )
        config.Settings.set(
            "mapGenerator/terrainSymmetry",
            self.terrainSymmetry.currentText(),
        )
        config.Settings.set(
            "mapGenerator/minResourceDensity",
            self.minResourceDensity.value(),
        )
        config.Settings.set(
            "mapGenerator/maxResourceDensity",
            self.maxResourceDensity.value(),
        )
        config.Settings.set(
            "mapGenerator/minReclaimDensity",
            self.minReclaimDensity.value(),
        )
        config.Settings.set(
            "mapGenerator/maxReclaimDensity",
            self.maxReclaimDensity.value(),
        )
        for spinner in self.spinners:
            config.Settings.set(
                f"mapGenerator/{spinner.objectName()}",
                spinner.value(),
            )
        self.done(1)

    @QtCore.pyqtSlot()
    def reset_mapgen_prefs(self) -> None:
        self.generationType.setCurrentIndex(0)
        self.mapSize.setValue(5.0)
        self.numberOfSpawns.setCurrentIndex(0)
        self.mapStyle.setCurrentIndex(0)

        for spinner in self.spinners:
            spinner.setValue(0)

    @QtCore.pyqtSlot()
    def generate_map(self):
        map_ = self.parent.client.map_generator.generateMap(
            args=self.set_arguments(),
        )
        if map_:
            self.parent.setupMapList()
            self.parent.set_map(map_)
            self.save_mapgen_prefs()

    def get_density(self, minval: int, maxval: int) -> float:
        return random.randrange(minval, maxval + 1) / 100

    def set_arguments(self) -> list[str]:
        args = []
        args.append("--map-size")
        args.append(str(self.map_size))
        args.append("--spawn-count")
        args.append(str(self.number_of_spawns))

        if self.generation_type != GenerationType.CASUAL:
            args.append(f"--{self.generation_type.value}")
            return args

        if (symmetry := self.terrainSymmetry.currentData()) != TerrainSymmtery.RANDOM:
            args.append("--terrain-symmetry")
            args.append(symmetry.value)

        if not self.useCustomStyleCheckBox.isChecked():
            if self.map_style != MapStyle.RANDOM:
                args.append("--style")
                args.append(self.map_style.value)
            return args

        resource_density = Density(
            self.minResourceDensity.value(),
            self.maxResourceDensity.value(),
        )
        args.append("--resource-density")
        args.append(str(resource_density.value()))

        reclaim_density = Density(
            self.minReclaimDensity.value(),
            self.maxReclaimDensity.value(),
        )
        args.append("--reclaim-density")
        args.append(str(reclaim_density.value()))

        for control, control_cls, argname in zip(
            (self.terrainStyle, self.textureStyle, self.resourceGenerator, self.propGenerator),
            (TerrainStyle, TextureStyle, ResourceStyle, PropStyle),
            ("--terrain-style", "--texture-style", "--resource-style", "--prop-style"),
        ):
            if control.currentData() == control_cls.RANDOM:
                continue
            args.append(argname)
            args.append(control.currentData().value)

        return args
