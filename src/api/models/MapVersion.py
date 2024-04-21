from __future__ import annotations

from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity


@dataclass
class MapSize:
    height_px: int
    width_px: int

    @property
    def width_km(self) -> int:
        return self.width_px // 51.2

    @property
    def height_km(self) -> int:
        return self.height_px // 51.2

    def __lt__(self, other: MapSize) -> bool:
        return self.height_px * self.width_px < other.height_px * other.width_px

    def __ge__(self, other: MapSize) -> bool:
        return not self.__lt__(other)

    def __str__(self) -> str:
        return f"{self.width_km} x {self.height_km} km"


@dataclass
class MapVersion(AbstractEntity):
    folder_name: str
    games_played: int
    description: str
    max_players: int
    size: MapSize
    version: int
    hidden: bool
    ranked: bool
    download_url: str
    thumbnail_url_small: str
    thumbnail_url_large: str
