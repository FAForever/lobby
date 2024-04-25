import logging

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class ReplaysApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/game')
