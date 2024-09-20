from src.api.models.Mod import Mod


class ModParser:

    @staticmethod
    def parse(mod_info: dict) -> Mod:
        return Mod(**mod_info)

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[Mod]:
        return [ModParser.parse(mod_info) for mod_info in api_result]
