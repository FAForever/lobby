from api.models.Map import Map
from api.models.MapType import MapType
from api.parsers.MapVersionParser import MapVersionParser
from api.parsers.PlayerParser import PlayerParser
from api.parsers.ReviewsSummaryParser import ReviewsSummaryParser


class MapParser:

    @staticmethod
    def parse(api_result: dict) -> Map:
        return Map(
            uid=api_result["id"],
            create_time=api_result["createTime"],
            update_time=api_result["updateTime"],
            display_name=api_result["displayName"],
            recommended=api_result["recommended"],
            author=PlayerParser.parse(api_result["author"]),
            reviews_summary=ReviewsSummaryParser.parse(api_result["reviewsSummary"]),
            games_played=api_result["gamesPlayed"],
            maptype=MapType.from_string(api_result["mapType"]),
        )

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[Map]:
        return [
            MapParser.parse_version(info, info["latestVersion"])
            for info in api_result
        ]

    @staticmethod
    def parse_version(map_info: dict, version_info: dict) -> Map:
        version = MapVersionParser.parse(version_info)
        return Map(
            uid=map_info["id"],
            create_time=map_info["createTime"],
            update_time=map_info["updateTime"],
            display_name=map_info["displayName"],
            recommended=map_info["recommended"],
            author=PlayerParser.parse(map_info["author"]),
            reviews_summary=ReviewsSummaryParser.parse(map_info["reviewsSummary"]),
            games_played=map_info["gamesPlayed"],
            maptype=MapType.from_string(map_info["mapType"]),
            version=version,
        )
