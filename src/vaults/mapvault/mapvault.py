import logging
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from stat import S_IWRITE

from PyQt5 import QtCore, QtWidgets

import util
from api.vaults_api import MapApiConnector, MapPoolApiConnector
from fa import maps
from vaults import luaparser
from vaults.mapvault.mapitem import MapItem
from vaults.vault import Vault

from .mapwidget import MapWidget

logger = logging.getLogger(__name__)


class MapVault(Vault):
    def __init__(self, client, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        Vault.__init__(self, client, *args, **kwargs)

        logger.debug("Map Vault tab instantiating")

        self.itemList.itemDoubleClicked.connect(self.itemClicked)
        self.client.lobby_info.mapVaultInfo.connect(self.mapInfo)
        self.client.authorized.connect(self.busy_entered)

        self.installed_maps = maps.getUserMaps()

        for type_ in ["Size"]:
            self.SortTypeList.addItem(type_)
        for type_ in ["Unranked Only", "Ranked Only", "Installed"]:
            self.ShowTypeList.addItem(type_)

        self.mapApiConnector = MapApiConnector(self.client.lobby_dispatch)
        self.mapPoolApiConnector = MapPoolApiConnector(
            self.client.lobby_dispatch,
        )
        self.apiConnector = self.mapApiConnector

        self.items_uid = "folderName"

        self.busy_entered()
        self.UIButton.hide()
        self.uploadButton.hide()

    def createItem(self, item_key: str) -> MapItem:
        return MapItem(self, item_key)

    @QtCore.pyqtSlot(dict)
    def mapInfo(self, message: dict) -> None:
        super().itemsInfo(message)

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
        self.updateVisibilities()

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
        self.updateVisibilities()

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def itemClicked(self, item):
        widget = MapWidget(self, item)
        widget.exec_()

    def requestMapPool(self, queueName, minRating):
        self.apiConnector = self.mapPoolApiConnector
        self.searchQuery = dict(
            include=(
                'mapVersion,mapVersion.map.latestVersion,'
                'mapVersion.reviewsSummary'
            ),
            filter=(
                'mapPool.matchmakerQueueMapPool.matchmakerQueue.'
                'technicalName=="{}";'
                '(mapPool.matchmakerQueueMapPool.minRating=le="{}",'
                'mapPool.matchmakerQueueMapPool.minRating=isnull="true")'
                .format(queueName, minRating)
            ),
        )
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
                            QtWidgets.QMessageBox.Yes,
                            QtWidgets.QMessageBox.No,
                        )
                    else:
                        uploadmap = QtWidgets.QMessageBox.Yes
                    if uploadmap == QtWidgets.QMessageBox.Yes:
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
            self.updateVisibilities()
        else:
            show = QtWidgets.QMessageBox.question(
                self.client,
                "Already got the Map",
                (
                    "Seems like you already have that map!<br/><b>Would you "
                    "like to see it?</b>"
                ),
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No,
            )
            if show == QtWidgets.QMessageBox.Yes:
                util.showDirInFileBrowser(maps.folderForMap(avail_name))

    @QtCore.pyqtSlot(str)
    def removeMap(self, folder):
        maps_folder = os.path.join(maps.getUserMapsFolder(), folder)
        if os.path.exists(maps_folder):
            shutil.rmtree(maps_folder)
            self.installed_maps.remove(folder)
            self.updateVisibilities()
