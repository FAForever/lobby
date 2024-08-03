from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


def api_response_empty(resp: dict) -> bool:
    wasnt_included = ("id" in resp and "type" in resp and len(resp) == 2)
    return not resp or wasnt_included


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def ensure_included_and_not_empty_or_none(cls, v: Any) -> Any:
        if isinstance(v, dict):
            if api_response_empty(v):
                return None
        elif isinstance(v, list):
            if (
                not v
                or len(list(filter(api_response_empty, v))) == len(v)
            ):
                return None
        return v
