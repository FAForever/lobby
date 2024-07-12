from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def ensure_included_and_not_empty_or_none(cls, v: Any) -> Any:
        if isinstance(v, dict):
            if not v or ("id" in v and "type" in v and len(v) == 2):
                return None
        elif isinstance(v, list) and not v:
            return None
        return v
