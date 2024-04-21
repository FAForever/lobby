from api.models.MapVersion import MapSize
from api.models.MapVersion import MapVersion


class MapVersionParser:

    @staticmethod
    def parse(version_info: dict) -> MapVersion:
        return MapVersion(
            uid=version_info["id"],
            create_time=version_info["createTime"],
            update_time=version_info["updateTime"],
            folder_name=version_info["folderName"],
            games_played=version_info["gamesPlayed"],
            description=version_info["description"],
            max_players=version_info["maxPlayers"],
            size=MapSize(version_info["height"], version_info["width"]),
            version=version_info["version"],
            hidden=version_info["hidden"],
            ranked=version_info["ranked"],
            download_url=version_info["downloadUrl"],
            thumbnail_url_small=version_info["thumbnailUrlSmall"],
            thumbnail_url_large=version_info["thumbnailUrlLarge"],
        )
