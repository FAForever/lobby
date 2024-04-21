from api.models.ReviewsSummary import ReviewsSummary


def _avoid_none(value: float | int | None) -> float | int:
    return value or 0


class ReviewsSummaryParser:

    @staticmethod
    def parse(reviews_info: dict) -> ReviewsSummary | None:
        if not reviews_info:
            return None

        return ReviewsSummary(
            positive=_avoid_none(reviews_info["positive"]),
            negative=_avoid_none(reviews_info["negative"]),
            score=_avoid_none(reviews_info["score"]),
            average_score=_avoid_none(reviews_info["averageScore"]),
            num_reviews=_avoid_none(reviews_info["reviews"]),
            lower_bound=_avoid_none(reviews_info["lowerBound"]),
        )
