from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel


class CoopMission(ConfiguredModel):
    xd:                  int = Field(alias="id")
    category:            str
    description:         str
    download_url:        str = Field(alias="downloadUrl")
    folder_name:         str = Field(alias="folderName")
    name:                str
    order:               int
    thumbnail_url_large: str = Field(alias="thumbnailUrlLarge")
    thumbnail_url_small: str = Field(alias="thumbnailUrlSmall")
    version:             int
