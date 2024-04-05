import logging

from api.ApiAccessors import DataApiAccessor
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class PlayerApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/player')
        self.dispatch = dispatch

    def requestDataForLeaderboard(
            self,
            leaderboardName: str,
            queryDict: dict | None = None,
    ) -> None:
        queryDict = queryDict or {}
        self.leaderboardName = leaderboardName
        self.get_by_query(queryDict, self.handleDataForLeaderboard)

    def handleDataForLeaderboard(self, message: dict) -> None:
        preparedData = dict(
            command='stats',
            type='player',
            leaderboardName=self.leaderboardName,
            values=message['data'],
            meta=message['meta'],
        )
        self.dispatch.dispatch(preparedData)

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
        preparedData = dict(
            command='alias_info',
            values=message['data'],
            meta=message['meta'],
        )
        self.dispatch.dispatch(preparedData)
