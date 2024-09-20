from __future__ import annotations

from pydantic import Field

from src.api.models.AbstractEntity import AbstractEntity
from src.api.models.AvatarAssignment import AvatarAssignment
from src.api.models.NameRecord import NameRecord


class Player(AbstractEntity):
    login:                  str
    user_agent:             str | None                    = Field(alias="userAgent")

    avatar_assignments:     list[AvatarAssignment] | None = Field(None, alias="avatarAssignments")
    names:                  list[NameRecord] | None       = Field(None)
