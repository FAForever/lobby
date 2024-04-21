from api.models.Player import Player


class PlayerParser:

    @staticmethod
    def parse(player_info: dict) -> Player | None:
        if not player_info:
            return None

        return Player(
            uid=player_info["id"],
            create_time=player_info["createTime"],
            update_time=player_info["updateTime"],
            login=player_info["login"],
            user_agent=player_info["userAgent"],
        )
