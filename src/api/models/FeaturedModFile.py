from pydantic import Field

from api.models.ConfiguredModel import ConfiguredModel


class FeaturedModFile(ConfiguredModel):
    xd:             str = Field(alias="id")
    version:        int
    group:          str
    name:           str
    md5:            str
    url:            str
    cacheable_url:  str = Field(alias="cacheableUrl")
    hmac_token:     str = Field(alias="hmacToken")
    hmac_parameter: str = Field(alias="hmacParameter")
