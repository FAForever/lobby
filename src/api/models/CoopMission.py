from pydantic import BaseModel
from pydantic import Field


class CoopMission(BaseModel):
    uid: int = Field(alias="id")
    category: str
    description: str
    download_url: str = Field(alias="downloadUrl")
    folder_name: str = Field(alias="folderName")
    name: str
    order: int
    thumbnail_url_large: str = Field(alias="thumbnailUrlLarge")
    thumbnail_url_small: str = Field(alias="thumbnailUrlSmall")
    version: int
