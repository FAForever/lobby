from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AbstractEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    xd: str = Field(alias="id")
    create_time: str = Field(alias="createTime")
    update_time: str = Field(alias="updateTime")
