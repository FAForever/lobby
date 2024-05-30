from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6 import QtCore

import util
from ui.busy_widget import BusyWidget
from vaults.vaultitem import VaultItemDelegate
from vaults.vaultitem import VaultListItem

if TYPE_CHECKING:
    from client._clientwindow import ClientWindow

logger = logging.getLogger(__name__)


FormClass, BaseClass = util.THEME.loadUiType("vaults/vault.ui")


class Vault(FormClass, BaseClass, BusyWidget):
    def __init__(self, client: ClientWindow, *args, **kwargs) -> None:
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.setupUi(self)
        self.client = client

        self.itemList.setItemDelegate(VaultItemDelegate(self))

        self.searchButton.clicked.connect(self.search)
        self.searchInput.returnPressed.connect(self.search)

        self.SortTypeList.setCurrentIndex(0)
        self.SortTypeList.currentIndexChanged.connect(self.sortChanged)
        self.ShowTypeList.currentIndexChanged.connect(self.showChanged)

        self.sortType = "alphabetical"
        self.showType = "all"
        self.searchString = ""
        self.searchQuery = {}
        self.apiConnector = None

        self.pageSize = self.quantityBox.value()
        self.pageNumber = 1

        self.goToPageButton.clicked.connect(
            lambda: self.goToPage(self.pageBox.value()),
        )
        self.pageBox.setValue(self.pageNumber)
        self.pageBox.valueChanged.connect(self.checkTotalPages)
        self.totalPages = None
        self.totalRecords = None
        self.quantityBox.valueChanged.connect(self.checkPageSize)
        self.nextButton.clicked.connect(
            lambda: self.goToPage(self.pageBox.value() + 1),
        )
        self.previousButton.clicked.connect(
            lambda: self.goToPage(self.pageBox.value() - 1),
        )
        self.firstButton.clicked.connect(lambda: self.goToPage(1))
        self.lastButton.clicked.connect(lambda: self.goToPage(self.totalPages))
        self.resetButton.clicked.connect(self.resetSearch)

        self._items = {}
        self._installed_items = {}

        for type_ in ["Upload Date", "Rating"]:
            self.SortTypeList.addItem(type_)

    @QtCore.pyqtSlot(int)
    def checkPageSize(self):
        self.pageSize = self.quantityBox.value()

    @QtCore.pyqtSlot(int)
    def checkTotalPages(self):
        if self.pageBox.value() > self.totalPages:
            self.pageBox.setValue(self.totalPages)

    def updateQuery(self, pageNumber):
        self.searchQuery['page[size]'] = self.pageSize
        self.searchQuery['page[number]'] = pageNumber
        self.searchQuery['page[totals]'] = None

    @QtCore.pyqtSlot(bool)
    def goToPage(self, page: int) -> None:
        if self.apiConnector is None:
            return

        self._items.clear()
        self.itemList.clear()
        self.pageBox.setValue(page)
        self.pageNumber = self.pageBox.value()
        self.updateQuery(self.pageNumber)
        self.apiConnector.request_data(self.searchQuery)
        self.update_visibilities()

    def create_item(self, item_key: str) -> VaultListItem:
        return VaultListItem(self, item_key)

    @QtCore.pyqtSlot(dict)
    def items_info(self, message: dict) -> None:
        for value in message["values"]:
            item_key = value.uid
            if item_key in self._items:
                item = self._items[item_key]
            else:
                item = self.create_item(value)
                self._items[item_key] = item
                self.itemList.addItem(item)
        self.itemList.sortItems(QtCore.Qt.SortOrder.DescendingOrder)
        self.processMeta(message["meta"])

    def processMeta(self, message: dict) -> None:
        self.totalPages = message['page']['totalPages']
        self.totalRecords = message['page']['totalRecords']
        if self.totalPages < 1:
            self.totalPages = 1
        self.labelTotalPages.setText(str(self.totalPages))

    @QtCore.pyqtSlot(bool)
    def resetSearch(self):
        self.searchString = ''
        self.searchInput.clear()
        self.searchQuery.clear()
        self.goToPage(1)

    def search(self):
        self.searchString = self.searchInput.text().lower()
        if self.searchString == '' or self.searchString.replace(' ', '') == '':
            self.resetSearch()
        else:
            self.searchString = self.searchString.strip()
            self.searchQuery = {"filter": f"displayName=='*{self.searchString}*'"}
            self.goToPage(1)

    @QtCore.pyqtSlot()
    def busy_entered(self):
        if not self._items:
            self.goToPage(self.pageNumber)

    def update_visibilities(self) -> None:
        logger.debug(
            f"Updating visibilities with sort {self.sortType!r} and visibility {self.showType!r}",
        )
        for item in self._items.values():
            item.update_visibility()
        self.itemList.sortItems(QtCore.Qt.SortOrder.DescendingOrder)
