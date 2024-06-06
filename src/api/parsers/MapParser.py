from api.models.Map import Map
from api.models.MapVersion import MapVersion


class MapParser:

    @staticmethod
    def parse(api_result: dict) -> Map:
        return Map(**api_result)

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[Map]:
        return [
            MapParser.parse_version(info, info["latestVersion"])
            for info in api_result
        ]

    @staticmethod
    def parse_version(map_info: dict, version_info: dict) -> Map:
        map_model = Map(**map_info)
        map_model.version = MapVersion(**version_info)
        return map_model
