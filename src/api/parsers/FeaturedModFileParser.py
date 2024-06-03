from api.models.FeaturedModFile import FeaturedModFile


class FeaturedModFileParser:
    @staticmethod
    def parse(api_result: dict) -> FeaturedModFile:
        return FeaturedModFile(**api_result)

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[FeaturedModFile]:
        return [FeaturedModFileParser.parse(file_info) for file_info in api_result]
