from api.models.FeaturedMod import FeaturedMod


class FeaturedModParser:

    @staticmethod
    def parse(data: dict) -> FeaturedMod:
        return FeaturedMod(
            name=data["technicalName"],
            fullname=data["displayName"],
            visible=data.get("visible", False),
            order=data.get("order", 0),
            description=data.get(
                "description",
                "<i>No description provided</i>",
            ),
        )

    @staticmethod
    def parse_many(data: list[dict]) -> list[FeaturedMod]:
        return [FeaturedModParser.parse(info) for info in data]
