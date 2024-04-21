from dataclasses import dataclass


@dataclass
class AbstractEntity:
    uid: str
    create_time: str
    update_time: str
