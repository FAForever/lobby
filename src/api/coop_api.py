from api.ApiAccessors import DataApiAccessor
from api.models.CoopResult import CoopResult
from api.models.CoopScenario import CoopScenario
from api.parsers.CoopResultParser import CoopResultParser
from api.parsers.CoopScenarioParser import CoopScenarioParser


class CoopApiAccessor(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__("/data/coopScenario")

    def request_coop_scenarios(self) -> None:
        self.requestData({"include": "maps"})

    def prepare_data(self, message: dict) -> dict[str, list[CoopScenario]]:
        return {"values": CoopScenarioParser.parse_many(message["data"])}


class CoopResultApiAccessor(DataApiAccessor):
    def __init__(self):
        super().__init__("/data/coopResult")

    def prepare_query_dict(self, mission: int) -> dict:
        return {
            "filter": f"mission=={mission}",
            "include": "game,game.playerStats.player",
            "sort": "duration",
            "page[size]": 1000,
        }

    def extend_filter(self, query_options: dict, filteroption: str) -> dict:
        cur_filters = query_options.get("filter", "")
        query_options["filter"] = ";".join((cur_filters, filteroption)).removeprefix(";")
        return query_options

    def request_coop_results(self, mission: int, player_count: int) -> None:
        default_query = self.prepare_query_dict(mission)
        query = self.extend_filter(default_query, f"playerCount=={player_count}")
        self.requestData(query)

    def request_coop_results_general(self, mission: int) -> None:
        self.requestData(self.prepare_query_dict(mission))

    def filter_unique_teams(self, results: list[CoopResult]) -> list[CoopResult]:
        unique_results = []
        unique_teams = set()
        for result in results:
            player_ids = [player_stat.player.xd for player_stat in result.game.player_stats]
            players_tuple = tuple(sorted(player_ids))
            if players_tuple not in unique_teams:
                unique_results.append(result)
            unique_teams.add(players_tuple)
        return unique_results

    def prepare_data(self, message: dict) -> dict[str, list[CoopResult]]:
        parsed = CoopResultParser.parse_many(message["data"])
        distinct = self.filter_unique_teams(parsed)
        return {"values": distinct}
