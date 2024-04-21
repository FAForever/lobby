from api.models.Map import Map
from api.models.MapPoolAssignment import MapPoolAssignment
from api.parsers.GeneratedMapParamsParser import GeneratedMapParamsParser
from api.parsers.MapParser import MapParser
from api.parsers.MapVersionParser import MapVersionParser


class MapPoolAssignmentParser:

    @staticmethod
    def parse(assignment_info: dict) -> MapPoolAssignment:
        if assignment_info["mapVersion"]:
            map_version = MapVersionParser.parse(assignment_info["mapVersion"])
            map_params = None
        elif assignment_info["mapParams"]:
            map_version = None
            map_params = GeneratedMapParamsParser.parse(assignment_info["mapParams"])

        return MapPoolAssignment(
            uid=assignment_info["id"],
            create_time=assignment_info["createTime"],
            update_time=assignment_info["updateTime"],
            map_version=map_version,
            map_params=map_params,
            weight=assignment_info["weight"],
        )

    @staticmethod
    def parse_many(assignment_info: list[dict]) -> list[MapPoolAssignment]:
        return [MapPoolAssignmentParser.parse(info) for info in assignment_info]

    @staticmethod
    def parse_to_map(assignment_info: dict) -> Map:
        pool = MapPoolAssignmentParser.parse(assignment_info)
        if pool.map_params is not None:
            return pool.map_params.to_map()
        if pool.map_version is not None:
            return MapParser.parse_version(
                assignment_info["mapVersion"]["map"],
                assignment_info["mapVersion"],
            )
        raise ValueError("MapPoolAssignment info does not contain mapVersion or mapParams")

    @staticmethod
    def parse_many_to_maps(assignment_info: list[dict]) -> list[Map]:
        return [MapPoolAssignmentParser.parse_to_map(info) for info in assignment_info]
