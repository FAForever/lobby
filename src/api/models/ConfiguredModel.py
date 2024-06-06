from pydantic import BaseModel
from pydantic import ConfigDict


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
