from api.models.LeaderboardRatingJournal import LeaderboardRatingJournal


class LeaderboardRatingJournalParser:

    @staticmethod
    def parse(api_result: dict) -> LeaderboardRatingJournal:
        return LeaderboardRatingJournal(**api_result)

    @staticmethod
    def parse_many(api_result: dict) -> list[LeaderboardRatingJournal]:
        return [LeaderboardRatingJournalParser.parse(entry) for entry in api_result["data"]]
