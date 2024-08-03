from __future__ import annotations

from api.models.AbstractEntity import AbstractEntity
from api.models.GeneratedMapParams import GeneratedMapParams
from api.models.MapVersion import MapVersion
from pydantic import Field


class MapPoolAssignment(AbstractEntity):
    map_params:  GeneratedMapParams | None = Field(None, alias="mapParams")
    map_version: MapVersion | None         = Field(None, alias="mapVersion")
    weight:      int
