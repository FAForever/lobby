from dataclasses import dataclass

from api.models.AbstractEntity import AbstractEntity


@dataclass
class Player(AbstractEntity):
    login: str
    user_agent: str
