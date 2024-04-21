from __future__ import annotations

from dataclasses import dataclass

from api.models.Map import Map
from api.models.MapType import MapType
from api.models.MapVersion import MapSize
from api.models.MapVersion import MapVersion


@dataclass
class GeneratedMapParams:
    name: str
    spawns: int
    size: int
    gen_version: str

    def to_map(self) -> Map:
        uid = f"neroxis_map_generator_{self.gen_version}_{self.name}_{self.spawns}_{self.size}"
        version = MapVersion(
            uid=uid,
            create_time="",
            update_time="",
            folder_name=uid,
            games_played=0,
            description="Randomly Generated Map",
            max_players=self.spawns,
            size=MapSize(self.size, self.size),
            version=self.gen_version,
            hidden=False,
            ranked=True,
            download_url="",
            thumbnail_url_small="",
            thumbnail_url_large="",
        )
        return Map(
            uid=uid,
            create_time="",
            update_time="",
            display_name=self.name,
            author=None,
            recommended=False,
            reviews_summary=None,
            games_played=0,
            maptype=MapType.SKIRMISH,
            version=version,
        )
