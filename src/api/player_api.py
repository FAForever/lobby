import logging

from PyQt6.QtCore import pyqtSignal

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class PlayerApiConnector(DataApiAccessor):
    alias_info = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__('/data/player')

    def requestDataForAliasViewer(self, nameToFind: str) -> None:
        queryDict = {
            'include': 'names',
            'filter': '(login=="{name}",names.name=="{name}")'.format(
                name=nameToFind,
            ),
            'fields[player]': 'login,names',
            'fields[nameRecord]': 'name,changeTime,player',
        }
        self.get_by_query(queryDict, self.handleDataForAliasViewer)

    def handleDataForAliasViewer(self, message: dict) -> None:
        self.alias_info.emit(message)
