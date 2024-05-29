from api.ApiAccessors import DataApiAccessor
from api.models.CoopScenario import CoopScenario


class CoopApiAccessor(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__("/data/coopScenario")

    def request_coop_scenarios(self) -> None:
        self.requestData({"include": "maps"})

    def prepare_data(self, message: dict) -> dict[str, list[CoopScenario]]:
        return {"values": [CoopScenario(**entry) for entry in message["data"]]}
