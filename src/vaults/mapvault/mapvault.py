from __future__ import annotations

import logging
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from stat import S_IWRITE
from typing import TYPE_CHECKING

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from src import util
from src.api.models.Map import Map
from src.api.vaults_api import MapApiConnector
from src.api.vaults_api import MapPoolApiConnector
from src.fa import maps
from src.vaults import luaparser
from src.vaults.mapvault.mapitem import MapListItem
from src.vaults.vault import Vault

if TYPE_CHECKING:
    from src.client._clientwindow import ClientWindow

from .mapwidget import MapWidget

logger = logging.getLogger(__name__)


class MapVault(Vault):
    def __init__(self, client: ClientWindow, *args, **kwargs) -> None:
        QtCore.QObject.__init__(self, *args, **kwargs)
        Vault.__init__(self, client, *args, **kwargs)

        logger.debug("Map Vault tab instantiating")

        self.itemList.itemDoubleClicked.connect(self.itemClicked)
        self.client.authorized.connect(self.busy_entered)

        self.installed_maps = maps.getUserMaps()

        for type_ in ["Size"]:
            self.SortTypeList.addItem(type_)
        for type_ in ["Unranked Only", "Ranked Only", "Installed"]:
            self.ShowTypeList.addItem(type_)

        self.mapApiConnector = MapApiConnector()
        self.mapPoolApiConnector = MapPoolApiConnector()
        self.mapApiConnector.data_ready.connect(self.mapInfo)
        self.mapPoolApiConnector.data_ready.connect(self.mapInfo)

        self.apiConnector = self.mapApiConnector

        self.busy_entered()
        self.UIButton.hide()
        self.uploadButton.hide()

    def create_item(self, item: Map) -> MapListItem:
        return MapListItem(self, item)

    @QtCore.pyqtSlot(dict)
    def mapInfo(self, message: dict) -> None:
        super().items_info(message)

    @QtCore.pyqtSlot(int)
    def sortChanged(self, index):
        if index == -1 or index == 0:
            self.sortType = "alphabetical"
        elif index == 1:
            self.sortType = "date"
        elif index == 2:
            self.sortType = "rating"
        elif index == 3:
            self.sortType = "size"
        self.update_visibilities()

    @QtCore.pyqtSlot(int)
    def showChanged(self, index):
        if index == -1 or index == 0:
            self.showType = "all"
        elif index == 1:
            self.showType = "unranked"
        elif index == 2:
            self.showType = "ranked"
        elif index == 3:
            self.showType = "installed"
        self.update_visibilities()

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def itemClicked(self, item: MapListItem) -> None:
        widget = MapWidget(self, item)
        widget.exec()

    def requestMapPool(self, queueName, minRating):
        self.apiConnector = self.mapPoolApiConnector
        self.searchQuery = {
            "filter": ";".join((
                f"mapPool.matchmakerQueueMapPool.matchmakerQueue.technicalName=={queueName}",
                (
                    f"(mapPool.matchmakerQueueMapPool.minRating=le={minRating!r},"
                    "mapPool.matchmakerQueueMapPool.minRating=isnull='true')"
                ),
            )),
        }
        self.goToPage(1)
        self.apiConnector = self.mapApiConnector

    @QtCore.pyqtSlot()
    def uploadMap(self):
        mapDir = QtWidgets.QFileDialog.getExistingDirectory(
            self.client,
            "Select the map directory to upload",
            maps.getUserMapsFolder(),
            QtWidgets.QFileDialog.ShowDirsOnly,
        )
        logger.debug("Uploading map from: " + mapDir)
        if mapDir != "":
            if maps.isMapFolderValid(mapDir):
                os.chmod(mapDir, S_IWRITE)
                mapName = os.path.basename(mapDir)
                # zipName = mapName.lower() + ".zip"

                scenariolua = luaparser.luaParser(
                    os.path.join(mapDir, maps.getScenarioFile(mapDir)),
                )
                scenarioInfos = scenariolua.parse(
                    {
                        'scenarioinfo>name': 'name',
                        'size': 'map_size',
                        'description': 'description',
                        'count:armies': 'max_players',
                        'map_version': 'version',
                        'type': 'map_type',
                        'teams>0>name': 'battle_type',
                    },
                    {'version': '1'},
                )

                if scenariolua.error:
                    logger.debug(
                        "There were {} errors and {} warnings".format(
                            scenariolua.errors,
                            scenariolua.warnings,
                        ),
                    )
                    logger.debug(scenariolua.errorMsg)
                    QtWidgets.QMessageBox.critical(
                        self.client,
                        "Lua parsing error",
                        (
                            "{}\nMap uploading cancelled."
                            .format(scenariolua.errorMsg)
                        ),
                    )
                else:
                    if scenariolua.warning:
                        uploadmap = QtWidgets.QMessageBox.question(
                            self.client,
                            "Lua parsing warning",
                            (
                                "{}\nDo you want to upload the map?"
                                .format(scenariolua.errorMsg)
                            ),
                            QtWidgets.QMessageBox.StandardButton.Yes,
                            QtWidgets.QMessageBox.StandardButton.No,
                        )
                    else:
                        uploadmap = QtWidgets.QMessageBox.StandardButton.Yes
                    if uploadmap == QtWidgets.QMessageBox.StandardButton.Yes:
                        savelua = luaparser.luaParser(
                            os.path.join(mapDir, maps.getSaveFile(mapDir)),
                        )
                        saveInfos = savelua.parse({
                            'markers>mass*>position': 'mass:__parent__',
                            'markers>hydro*>position': 'hydro:__parent__',
                            'markers>army*>position': 'army:__parent__',
                        })
                        if savelua.error or savelua.warning:
                            logger.debug(
                                "There were {} errors and {} warnings"
                                .format(
                                    scenariolua.errors,
                                    scenariolua.warnings,
                                ),
                            )
                            logger.debug(scenariolua.errorMsg)

                        self.__preparePositions(
                            saveInfos,
                            scenarioInfos["map_size"],
                        )

                        tmpFile = maps.processMapFolderForUpload(
                            mapDir,
                            saveInfos,
                        )
                        if not tmpFile:
                            QtWidgets.QMessageBox.critical(
                                self.client,
                                "Map uploading error",
                                (
                                    "Couldn't make previews for {}\n"
                                    "Map uploading cancelled.".format(mapName)
                                ),
                            )
                            return None

                        qfile = QtCore.QFile(tmpFile.name)

                        # TODO: implement uploading via API
                        ...
                        # removing temporary files
                        qfile.remove()
            else:
                QtWidgets.QMessageBox.information(
                    self.client,
                    "Map selection",
                    "This folder doesn't contain valid map data.",
                )

    @QtCore.pyqtSlot(str)
    def downloadMap(self, link):
        link = urllib.parse.unquote(link)
        name = maps.link2name(link)
        alt_name = name.replace(" ", "_")
        avail_name = None
        if maps.isMapAvailable(name):
            avail_name = name
        elif maps.isMapAvailable(alt_name):
            avail_name = alt_name
        if avail_name is None:
            maps.downloadMap(name)
            self.installed_maps.append(name)
            self.update_visibilities()
        else:
            show = QtWidgets.QMessageBox.question(
                self.client,
                "Already got the Map",
                (
                    "Seems like you already have that map!<br/><b>Would you "
                    "like to see it?</b>"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if show == QtWidgets.QMessageBox.StandardButton.Yes:
                util.showDirInFileBrowser(maps.folderForMap(avail_name))

    @QtCore.pyqtSlot(str)
    def removeMap(self, folder):
        maps_folder = os.path.join(maps.getUserMapsFolder(), folder)
        if os.path.exists(maps_folder):
            shutil.rmtree(maps_folder)
            self.installed_maps.remove(folder)
            self.update_visibilities()
