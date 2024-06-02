from api.models.ModVersion import ModVersion


class ModVersionParser:

    @staticmethod
    def parse(api_result: dict) -> ModVersion:
        return ModVersion(**api_result)
