from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def ensure_not_empty_dict(cls, v: Any) -> Any:
        if isinstance(v, dict) and not v:
            return None
        return v
