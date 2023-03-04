import logging

from api.ApiBase import ApiBase

logger = logging.getLogger(__name__)


class LeaderboardRatingApiConnector(ApiBase):
    def __init__(self, dispatch, leaderboardName):
        ApiBase.__init__(self, '/data/leaderboardRating')
        self.dispatch = dispatch
        self.leadeboardName = leaderboardName

    def requestData(self, queryDict={}):
        self.request(queryDict, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = dict(
            command='stats',
            type='leaderboardRating',
            leaderboardName=self.leadeboardName,
            values=message["data"],
            meta=message["meta"],
        )
        self.dispatch.dispatch(preparedData)


class LeaderboardApiConnector(ApiBase):
    def __init__(self, dispatch=None):
        ApiBase.__init__(self, '/data/leaderboard')
        self.dispatch = dispatch

    def requestData(self, queryDict={}):
        self.request(queryDict, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = dict(
            command='stats',
            type='leaderboard',
            values=message["data"],
            meta=message["meta"],
        )
        self.dispatch.dispatch(preparedData)
