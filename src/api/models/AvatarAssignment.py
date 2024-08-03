from api.models.AbstractEntity import AbstractEntity
from api.models.Avatar import Avatar
from pydantic import Field


class AvatarAssignment(AbstractEntity):
    expires_at: str | None    = Field(alias="expiresAt")
    selected:   bool

    avatar:     Avatar        = Field(None)
