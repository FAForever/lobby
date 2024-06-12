from api.models.LeaderboardRating import LeaderboardRating


class LeaderboardRatingParser:

    @staticmethod
    def parse(api_result: dict) -> LeaderboardRating:
        return LeaderboardRating(**api_result)

    @staticmethod
    def parse_many(api_result: dict) -> list[LeaderboardRating]:
        return [LeaderboardRatingParser.parse(entry) for entry in api_result["data"]]
