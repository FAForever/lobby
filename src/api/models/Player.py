from __future__ import annotations

from api.models.AbstractEntity import AbstractEntity
from api.models.AvatarAssignment import AvatarAssignment
from api.models.NameRecord import NameRecord
from pydantic import Field


class Player(AbstractEntity):
    login:                  str
    user_agent:             str | None                    = Field(alias="userAgent")

    avatar_assignments:     list[AvatarAssignment] | None = Field(None, alias="avatarAssignments")
    names:                  list[NameRecord] | None       = Field(None)
