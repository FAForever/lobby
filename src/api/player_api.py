import logging

from PyQt6.QtCore import pyqtSignal

from api.ApiAccessors import DataApiAccessor
from api.models.Player import Player

logger = logging.getLogger(__name__)


class PlayerApiConnector(DataApiAccessor):
    alias_info = pyqtSignal(dict)
    player_ready = pyqtSignal(Player)

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

    def request_player(self, player_id: str) -> None:
        query = {
            "include": "avatarAssignments.avatar,names",
            "filter": f"id=={player_id}",
        }
        self.get_by_query(query, self.handle_player)

    def handle_player(self, message: dict) -> None:
        player, = message["data"]
        self.player_ready.emit(Player(**player))
