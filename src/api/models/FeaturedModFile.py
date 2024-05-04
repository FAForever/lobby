from dataclasses import dataclass


@dataclass
class FeaturedModFile:
    uid: str
    version: int
    group: str
    name: str
    md5: str
    url: str
    cacheable_url: str
    hmac_token: str
    hmac_parameter: str
