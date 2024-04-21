from dataclasses import dataclass


@dataclass
class ReviewsSummary:
    positive: float
    negative: float
    score: float
    average_score: float
    num_reviews: int
    lower_bound: float
