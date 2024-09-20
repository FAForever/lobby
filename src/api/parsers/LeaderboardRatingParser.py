from src.api.models.LeaderboardRating import LeaderboardRating


class LeaderboardRatingParser:

    @staticmethod
    def parse(api_result: dict) -> LeaderboardRating:
        return LeaderboardRating(**api_result)

    @staticmethod
    def parse_many(api_result: dict) -> list[LeaderboardRating]:
        return sorted(
            [LeaderboardRatingParser.parse(entry) for entry in api_result["data"]],
            key=lambda rating: rating.leaderboard.order() if rating.leaderboard is not None else 0,
        )
