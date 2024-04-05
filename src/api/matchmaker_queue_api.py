import logging

from api.ApiAccessors import DataApiAccessor
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class matchmakerQueueApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/matchmakerQueue')
        self.dispatch = dispatch

    def requestData(self, queryDict: dict | None = None) -> None:
        queryDict = queryDict or {}
        self.get_by_query(queryDict, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = {
            "command": "matchmaker_queue_info",
            "values": [],
            "meta": message["meta"],
        }
        for queue in message["data"]:
            preparedQueue = {
                "technicalName": queue["technicalName"],
                "ratingType": queue["leaderboard"]["technicalName"],
                "id": queue["id"],
                "leaderboardId": queue["leaderboard"]["id"],
            }
            preparedData["values"].append(preparedQueue)
        self.dispatch.dispatch(preparedData)
