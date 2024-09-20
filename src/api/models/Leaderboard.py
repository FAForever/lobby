from __future__ import annotations

from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity


class Leaderboard(AbstractEntity):
    description:     str = Field(alias="descriptionKey")
    name:            str = Field(alias="nameKey")
    technical_name:  str = Field(alias="technicalName")

    @property
    def pretty_name(self) -> str:
        return self._pretty_names().get(self.technical_name, self.technical_name)

    def _pretty_names(self) -> dict[str, str]:
        return {
            "global": "Global",
            "ladder_1v1": "Ladder",
            "tmm_2v2": "2v2",
            "tmm_3v3": "3v3",
            "tmm_4v4_full_share": "4v4 (Full Share)",
            "tmm_4v4_share_until_death": "4v4 (No Share)",
        }

    def order(self) -> int:
        try:
            return list(self._pretty_names()).index(self.technical_name)
        except ValueError:
            return 0

    def __lt__(self, other: Leaderboard) -> bool:
        return self.order() < other.order()

    def __ge__(self, other: Leaderboard) -> bool:
        return not self.__lt__(other)
