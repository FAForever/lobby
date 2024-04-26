from dataclasses import dataclass


@dataclass
class FeaturedMod:
    name: str
    fullname: str
    visible: bool
    order: int
    description: str
