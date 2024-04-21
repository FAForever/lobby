from api.models.Map import Map
from src.api.models.GeneratedMapParams import GeneratedMapParams


class GeneratedMapParamsParser:

    @staticmethod
    def parse(params_info: dict) -> GeneratedMapParams:
        return GeneratedMapParams(
            name=params_info["type"],
            spawns=params_info["spawns"],
            size=params_info["size"],
            gen_version=params_info["version"],
        )

    @staticmethod
    def parse_to_map(params_info: dict) -> Map:
        return GeneratedMapParamsParser.parse(params_info).to_map()
