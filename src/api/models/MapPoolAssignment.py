from __future__ import annotations

from pydantic import Field
from pydantic import field_validator

from api.models.AbstractEntity import AbstractEntity
from api.models.GeneratedMapParams import GeneratedMapParams
from api.models.MapVersion import MapVersion


class MapPoolAssignment(AbstractEntity):
    map_params:  GeneratedMapParams | None = Field(None, alias="mapParams")
    map_version: MapVersion | None         = Field(None, alias="mapVersion")
    weight:      int

    @field_validator("map_params", mode="before")
    @classmethod
    def validate_map_params(cls, value: dict) -> GeneratedMapParams | None:
        if not value:
            return None
        return GeneratedMapParams(**value)

    @field_validator("map_version", mode="before")
    @classmethod
    def validate_map_version(cls, value: dict) -> MapVersion | None:
        if not value:
            return None
        return MapVersion(**value)
