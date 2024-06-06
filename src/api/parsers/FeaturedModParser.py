from api.models.FeaturedMod import FeaturedMod


class FeaturedModParser:

    @staticmethod
    def parse(data: dict) -> FeaturedMod:
        return FeaturedMod(**data)

    @staticmethod
    def parse_many(data: list[dict]) -> list[FeaturedMod]:
        return [FeaturedModParser.parse(info) for info in data]
