from api.models.AbstractEntity import AbstractEntity


class Avatar(AbstractEntity):
    filename: str
    tooltip:  str
    url:      str
