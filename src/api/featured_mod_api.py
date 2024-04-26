import logging

from api.ApiAccessors import DataApiAccessor
from api.parsers.FeaturedModParser import FeaturedModParser

logger = logging.getLogger(__name__)


class FeaturedModApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/featuredMod')

    def prepare_data(self, message: dict) -> None:
        return {"values": FeaturedModParser.parse_many(message["data"])}
