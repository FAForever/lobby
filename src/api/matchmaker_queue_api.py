import logging

from src.api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class MatchmakerQueueApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/matchmakerQueue')

    def prepare_data(self, message: dict) -> None:
        prepared_data = {
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
            prepared_data["values"].append(preparedQueue)
        return prepared_data
