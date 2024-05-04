from api.models.FeaturedModFile import FeaturedModFile


class FeaturedModFileParser:
    @staticmethod
    def parse(api_result: dict) -> FeaturedModFile:
        return FeaturedModFile(
            uid=api_result["id"],
            version=api_result["version"],
            group=api_result["group"],
            name=api_result["name"],
            md5=api_result["md5"],
            url=api_result["url"],
            cacheable_url=api_result["cacheableUrl"],
            hmac_token=api_result["hmacToken"],
            hmac_parameter=api_result["hmacParameter"],
        )

    @staticmethod
    def parse_many(api_result: list[dict]) -> list[FeaturedModFile]:
        return [FeaturedModFileParser.parse(file_info) for file_info in api_result]
