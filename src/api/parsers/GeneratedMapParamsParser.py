from src.api.models.GeneratedMapParams import GeneratedMapParams
from src.api.models.Map import Map


class GeneratedMapParamsParser:

    @staticmethod
    def parse(params_info: dict) -> GeneratedMapParams:
        return GeneratedMapParams(**params_info)

    @staticmethod
    def parse_to_map(params_info: dict) -> Map:
        return GeneratedMapParamsParser.parse(params_info).to_map()
