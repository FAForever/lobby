from dataclasses import dataclass


@dataclass
class FeaturedMod:
    uid: str
    name: str
    fullname: str
    visible: bool
    order: int
    description: str
