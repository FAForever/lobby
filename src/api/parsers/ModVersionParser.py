from api.models.ModVersion import ModType
from api.models.ModVersion import ModVersion


class ModVersionParser:

    @staticmethod
    def parse(api_result: dict) -> ModVersion:
        return ModVersion(
            uid=api_result["uid"],
            create_time=api_result["createTime"],
            update_time=api_result["updateTime"],
            description=api_result["description"],
            download_url=api_result["downloadUrl"],
            filename=api_result["filename"],
            hidden=api_result["hidden"],
            ranked=api_result["ranked"],
            thumbnail_url=api_result["thumbnailUrl"],
            modtype=ModType.from_string(api_result["type"]),
            version=api_result["version"],
        )
