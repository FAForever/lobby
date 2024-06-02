from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from api.models.Map import Map
from api.models.MapType import MapType
from api.models.MapVersion import MapVersion


class GeneratedMapParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name:        str = Field(alias="type")
    spawns:      int
    size:        int
    gen_version: str = Field(alias="version")

    def to_map(self) -> Map:
        uid = f"neroxis_map_generator_{self.gen_version}_{self.name}_{self.spawns}_{self.size}"
        version = MapVersion(
            xd=uid,
            create_time="",
            update_time="",
            folder_name=uid,
            games_played=0,
            description="Randomly Generated Map",
            max_players=self.spawns,
            height=self.size,
            width=self.size,
            version=self.gen_version,
            hidden=False,
            ranked=True,
            download_url="",
            thumbnail_url_small="",
            thumbnail_url_large="",
        )
        return Map(
            xd=uid,
            create_time="",
            update_time="",
            display_name=self.name,
            author=None,
            recommended=False,
            reviews_summary=None,
            games_played=0,
            map_type=MapType.SKIRMISH.value,
            version=version,
        )
