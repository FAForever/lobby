from src.api.models.CoopScenario import CoopScenario


class CoopScenarioParser:
    @staticmethod
    def parse(api_result: dict) -> CoopScenario:
        return CoopScenario(**api_result)

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[CoopScenario]:
        return [CoopScenarioParser.parse(entry) for entry in api_result]
