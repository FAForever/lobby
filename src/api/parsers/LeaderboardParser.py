from operator import methodcaller

from api.models.Leaderboard import Leaderboard


class LeaderboardParser:

    @staticmethod
    def parse(api_result: dict) -> Leaderboard:
        return Leaderboard(**api_result)

    @staticmethod
    def parse_many(api_result: dict) -> list[Leaderboard]:
        return sorted(
            [LeaderboardParser.parse(entry) for entry in api_result["data"]],
            key=methodcaller("order"),
        )
