from src.api.models.MapVersion import MapVersion


class MapVersionParser:

    @staticmethod
    def parse(version_info: dict) -> MapVersion:
        return MapVersion(**version_info)
