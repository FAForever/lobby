from api.models.Map import Map
from api.models.MapPoolAssignment import MapPoolAssignment
from api.parsers.MapParser import MapParser


class MapPoolAssignmentParser:

    @staticmethod
    def parse(assignment_info: dict) -> MapPoolAssignment:
        return MapPoolAssignment(**assignment_info)

    @staticmethod
    def parse_many(assignment_info: list[dict]) -> list[MapPoolAssignment]:
        return [MapPoolAssignmentParser.parse(info) for info in assignment_info]

    @staticmethod
    def parse_to_map(assignment_info: dict) -> Map:
        pool = MapPoolAssignmentParser.parse(assignment_info)
        if pool.map_params is not None:
            return pool.map_params.to_map()
        if pool.map_version is not None:
            map_model = MapParser.parse(assignment_info["mapVersion"]["map"])
            map_model.version = pool.map_version
            return map_model
        raise ValueError("MapPoolAssignment info does not contain mapVersion or mapParams")

    @staticmethod
    def parse_many_to_maps(assignment_info: list[dict]) -> list[Map]:
        return [MapPoolAssignmentParser.parse_to_map(info) for info in assignment_info]
