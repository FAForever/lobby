from __future__ import annotations

from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.GeneratedMapParams import GeneratedMapParams
from src.api.models.MapVersion import MapVersion


class MapPoolAssignment(AbstractEntity):
    map_params:  GeneratedMapParams | None = Field(None, alias="mapParams")
    map_version: MapVersion | None         = Field(None, alias="mapVersion")
    weight:      int
