from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from src import util
from src.downloadManager import DownloadRequest
from src.downloadManager import MapLargePreviewDownloader
from src.fa import maps
from src.mapGenerator import mapgenUtils
from src.vaults.mapvault.mapitem import MapListItem

if TYPE_CHECKING:
    from src.vaults.mapvault.mapvault import MapVault

FormClass, BaseClass = util.THEME.loadUiType("vaults/mapvault/map.ui")


class MapWidget(FormClass, BaseClass):
    ICONSIZE = QtCore.QSize(256, 256)

    def __init__(self, parent: MapVault, list_item: MapListItem, *args, **kwargs) -> None:
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)
        self.parent = parent

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        self._map = list_item.item_info
        self.map_version = list_item.item_version
        self.setWindowTitle(self._map.display_name)

        self.Title.setText(self._map.display_name)
        self.Description.setText(self.map_version.description)
        maptext = ""
        if not self.map_version.ranked:
            maptext = "Unranked map\n"
        self.Info.setText(f"{maptext} Uploaded {self.map_version.create_time}")
        self.Players.setText(f"Maximum players: {self.map_version.max_players}")
        self.Size.setText(f"Size: {self.map_version.size}")
        self._preview_dler = MapLargePreviewDownloader(util.MAP_PREVIEW_LARGE_DIR)
        self._map_dl_request = DownloadRequest()
        self._map_dl_request.done.connect(self._on_preview_downloaded)

        # Ensure that pixmap is set
        self.Picture.setPixmap(util.THEME.pixmap("games/unknown_map.png"))
        self.update_preview()

        if maps.isBase(self.map_version.folder_name):
            self.DownloadButton.setText("This is a base map")
            self.DownloadButton.setEnabled(False)
        elif mapgenUtils.isGeneratedMap(self.map_version.folder_name):
            self.DownloadButton.setEnabled(False)
        elif maps.isMapAvailable(self.map_version.folder_name):
            self.DownloadButton.setText("Remove Map")

        self.DownloadButton.clicked.connect(self.download)

    def load_stylesheet(self):
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    @QtCore.pyqtSlot()
    def download(self) -> None:
        if not maps.isMapAvailable(self.map_version.folder_name):
            self.parent.downloadMap(self.map_version.download_url)
            self.done(1)
        else:
            show = QtWidgets.QMessageBox.question(
                self.parent.client,
                "Delete Map",
                "Are you sure you want to delete this map?",
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if show == QtWidgets.QMessageBox.StandardButton.Yes:
                self.parent.removeMap(self.map_version.folder_name)
                self.done(1)

    def update_preview(self) -> None:
        imgPath = os.path.join(util.MAP_PREVIEW_LARGE_DIR, f"{self.map_version.folder_name}.png")
        if os.path.isfile(imgPath):
            pix = QtGui.QPixmap(imgPath).scaled(self.ICONSIZE)
            self.Picture.setPixmap(pix)
        elif mapgenUtils.isGeneratedMap(self.map_version.folder_name):
            self.Picture.setPixmap(util.THEME.pixmap("games/generated_map.png"))
        else:
            self._preview_dler.download_preview(
                self.map_version.folder_name,
                self._map_dl_request,
            )

    def _on_preview_downloaded(self, mapname, result: tuple[str, bool]) -> None:
        filename, themed = result
        pixmap = util.THEME.pixmap(filename, themed)
        if themed:
            self.Picture.setPixmap(pixmap)
        else:
            self.Picture.setPixmap(pixmap.scaled(self.ICONSIZE))
