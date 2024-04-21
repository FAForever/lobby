from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity
from api.models.GeneratedMapParams import GeneratedMapParams
from api.models.MapVersion import MapVersion


@dataclass
class MapPoolAssignment(AbstractEntity):
    map_params: GeneratedMapParams | None
    map_version: MapVersion | None
    weight: int
