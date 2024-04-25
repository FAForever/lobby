import logging

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class LeaderboardRatingApiConnector(DataApiAccessor):
    def __init__(self, leaderboard_name: str) -> None:
        super().__init__('/data/leaderboardRating')
        self.leaderboard_name = leaderboard_name

    def prepare_data(self, message: dict) -> None:
        message["leaderboard"] = self.leaderboard_name
        return message


class LeaderboardApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/leaderboard')
