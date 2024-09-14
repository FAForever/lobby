from src.api.models.ReviewsSummary import ReviewsSummary


class ReviewsSummaryParser:

    @staticmethod
    def parse(reviews_info: dict) -> ReviewsSummary | None:
        if not reviews_info:
            return None
        return ReviewsSummary(**reviews_info)
