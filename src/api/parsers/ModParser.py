from api.models.Mod import Mod
from api.parsers.ModVersionParser import ModVersionParser
from api.parsers.PlayerParser import PlayerParser
from api.parsers.ReviewsSummaryParser import ReviewsSummaryParser


class ModParser:

    @staticmethod
    def parse(mod_info: dict) -> Mod:
        return Mod(
            uid=mod_info["id"],
            create_time=mod_info["createTime"],
            update_time=mod_info["updateTime"],
            display_name=mod_info["displayName"],
            recommended=mod_info["recommended"],
            author=mod_info["author"],
            reviews_summary=ReviewsSummaryParser.parse(mod_info["reviewsSummary"]),
            uploader=PlayerParser.parse(mod_info["uploader"]),
            version=ModVersionParser.parse(mod_info["latestVersion"]),
        )

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[Mod]:
        return [ModParser.parse(mod_info) for mod_info in api_result]
