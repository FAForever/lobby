import logging

from api.ApiAccessors import DataApiAccessor
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class LeaderboardRatingApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher, leaderboardName: str) -> None:
        super().__init__('/data/leaderboardRating')
        self.dispatch = dispatch
        self.leadeboardName = leaderboardName

    def requestData(self, queryDict: dict | None = None) -> None:
        queryDict = queryDict or {}
        self.get_by_query(queryDict, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = dict(
            command='stats',
            type='leaderboardRating',
            leaderboardName=self.leadeboardName,
            values=message["data"],
            meta=message["meta"],
        )
        self.dispatch.dispatch(preparedData)


class LeaderboardApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher | None = None) -> None:
        super().__init__('/data/leaderboard')
        self.dispatch = dispatch

    def requestData(self, queryDict: dict | None = None) -> None:
        queryDict = queryDict or {}
        self.get_by_query(queryDict, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = dict(
            command='stats',
            type='leaderboard',
            values=message["data"],
            meta=message["meta"],
        )
        self.dispatch.dispatch(preparedData)
