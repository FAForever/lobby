from api.models.CoopResult import CoopResult


class CoopResultParser:
    @staticmethod
    def parse(api_result: dict) -> None:
        return CoopResult(**api_result)

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[CoopResult]:
        return [CoopResultParser.parse(entry) for entry in api_result]
