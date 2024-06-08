from api.models.Player import Player


class PlayerParser:

    @staticmethod
    def parse(player_info: dict) -> Player | None:
        if not player_info:
            return None

        return Player(**player_info)
