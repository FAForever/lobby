from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel


class AbstractEntity(ConfiguredModel):
    xd: str = Field(alias="id")
    create_time: str = Field(alias="createTime")
    update_time: str = Field(alias="updateTime")
