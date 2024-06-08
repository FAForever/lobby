from __future__ import annotations

from pydantic import Field

from api.models.AbstractEntity import AbstractEntity


class Player(AbstractEntity):
    login:      str
    user_agent: str | None = Field(alias="userAgent")
